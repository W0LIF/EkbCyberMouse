from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from api.app.models import Order

class SqlOrdersRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_many(
        self,
        date: str,
        orders: list[Order],
        *,
        replace_existing: bool = True,
        commit: bool = True,
    ) -> int:
        """Загружает наряды на день."""
        if replace_existing:
            await self.session.execute(
                text("DELETE FROM orders WHERE order_id LIKE :prefix"),
                {"prefix": f"ORD-{date.replace('-', '')}-%"}
            )
        
        count = 0
        for o in orders:
            await self.session.execute(
                text("""
                    INSERT INTO orders (order_id, work_type_code, technology, building_id, address, lat, lon, building_type, requires_height, access_node_id, registered_at, slot_start, slot_end, latest_start, deadline, req_ont, req_router, req_stb, is_repeat, previous_order_id, status)
                    VALUES (:id, :wt, :tech, :bld, :addr, :lat, :lon, :b_type, :req_h, :node, :reg_at, :slot_s, :slot_e, :lat_s, :deadline, :req_ont, :req_router, :req_stb, :is_rep, :prev, 'pending')
                    ON CONFLICT (order_id) DO UPDATE SET
                        work_type_code = EXCLUDED.work_type_code,
                        technology = EXCLUDED.technology,
                        building_id = EXCLUDED.building_id,
                        address = EXCLUDED.address,
                        lat = EXCLUDED.lat,
                        lon = EXCLUDED.lon,
                        building_type = EXCLUDED.building_type,
                        requires_height = EXCLUDED.requires_height,
                        access_node_id = EXCLUDED.access_node_id,
                        registered_at = EXCLUDED.registered_at,
                        slot_start = EXCLUDED.slot_start,
                        slot_end = EXCLUDED.slot_end,
                        latest_start = EXCLUDED.latest_start,
                        deadline = EXCLUDED.deadline,
                        req_ont = EXCLUDED.req_ont,
                        req_router = EXCLUDED.req_router,
                        req_stb = EXCLUDED.req_stb,
                        is_repeat = EXCLUDED.is_repeat,
                        previous_order_id = EXCLUDED.previous_order_id
                """),
                {
                    "id": o.order_id, "wt": o.work_type_code, "tech": o.technology, "bld": o.building_id,
                    "addr": o.address, "lat": o.lat, "lon": o.lon, "b_type": o.building_type,
                    "req_h": o.requires_height, "node": o.access_node_id,
                    "reg_at": datetime.fromisoformat(o.registered_at.isoformat()) if isinstance(o.registered_at, str) else o.registered_at,
                    "slot_s": datetime.fromisoformat(o.slot.start.isoformat()) if isinstance(o.slot.start, str) else o.slot.start,
                    "slot_e": datetime.fromisoformat(o.slot.end.isoformat()) if isinstance(o.slot.end, str) else o.slot.end,
                    "lat_s": datetime.fromisoformat(o.latest_start.isoformat()) if isinstance(o.latest_start, str) else o.latest_start,
                    "deadline": datetime.fromisoformat(o.deadline.isoformat()) if isinstance(o.deadline, str) else o.deadline,
                    "req_ont": o.required_equipment.ONT, "req_router": o.required_equipment.ROUTER, "req_stb": o.required_equipment.STB,
                    "is_rep": o.is_repeat, "prev": o.previous_order_id
                }
            )
            fact = o.fact
            if (
                fact is not None
                and fact.outcome == "COMPLETED"
                and fact.actual_duration_min is not None
                and fact.actual_duration_min > 0
            ):
                await self.session.execute(
                    text("""
                        INSERT INTO order_facts (
                            order_id, work_type_code, technology,
                            actual_duration_min, occurred_at
                        )
                        VALUES (:id, :wt, :tech, :duration, :occurred_at)
                        ON CONFLICT (order_id) DO UPDATE SET
                            work_type_code = EXCLUDED.work_type_code,
                            technology = EXCLUDED.technology,
                            actual_duration_min = EXCLUDED.actual_duration_min,
                            occurred_at = EXCLUDED.occurred_at
                    """),
                    {
                        "id": o.order_id,
                        "wt": o.work_type_code,
                        "tech": o.technology,
                        "duration": fact.actual_duration_min,
                        "occurred_at": fact.actual_start or o.registered_at,
                    },
                )
            count += 1
        
        if commit:
            await self.session.commit()
        return count

    async def get_by_date(self, date: str) -> list[dict]:
        """Возвращает все наряды на конкретный день."""
        date_str = date.replace("-", "")
        result = await self.session.execute(
            text("""
                SELECT order_id, work_type_code, technology, building_id, address, lat, lon, 
                       building_type, requires_height, access_node_id, registered_at, 
                       slot_start, slot_end, latest_start, deadline, 
                       req_ont, req_router, req_stb, is_repeat, previous_order_id, status,
                       assigned_staff_id, planned_start, planned_end
                FROM orders 
                WHERE order_id LIKE :prefix
            """),
            {"prefix": f"ORD-{date_str}-%"}
        )
        return [dict(row) for row in result.mappings()]

    async def get_duration_history(self) -> list[dict]:
        result = await self.session.execute(
            text("""
                SELECT work_type_code, technology, actual_duration_min
                FROM order_facts
                WHERE actual_duration_min > 0
            """)
        )
        return [dict(row) for row in result.mappings()]

    async def get_by_id(self, date: str, order_id: str) -> dict | None:
        result = await self.session.execute(
            text("SELECT * FROM orders WHERE order_id = :oid"),
            {"oid": order_id}
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def update_status(self, date: str, order_id: str, status: str, **kwargs) -> None:
        set_clause = "status = :status"
        params = {"status": status, "oid": order_id}
        
        for key, value in kwargs.items():
            set_clause += f", {key} = :{key}"
            params[key] = value
            
        await self.session.execute(
            text(f"UPDATE orders SET {set_clause} WHERE order_id = :oid"),
            params
        )
        await self.session.commit()

    async def get_by_node_and_window(self, node_id: str, from_dt: datetime, to_dt: datetime) -> list[dict]:
        """Для ПГП: ищем наряды с одного узла за последние 60 минут."""
        result = await self.session.execute(
            text("""
                SELECT * FROM orders 
                WHERE access_node_id = :node 
                  AND registered_at >= :from_dt 
                  AND registered_at <= :to_dt
            """),
            {"node": node_id, "from_dt": from_dt, "to_dt": to_dt}
        )
        return [dict(row) for row in result.mappings()]