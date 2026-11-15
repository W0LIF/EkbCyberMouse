from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.models import ReferenceData, Staff, ServiceCenter, AccessNode, WorkType, Building
import json

def _parse_json(val):
    """PostgreSQL возвращает JSONB как строку, Pydantic ждет dict."""
    if isinstance(val, str):
        return json.loads(val)
    return val

class SqlReferenceRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def replace_all(self, data: ReferenceData) -> None:
        """Полностью заменяет справочники."""
        await self.session.execute(
            text(
                "TRUNCATE TABLE alerts, events, plan_versions, days, orders, "
                "service_centers, staff, access_node_buildings, access_nodes, "
                "buildings, work_types RESTART IDENTITY CASCADE"
            )
        )
        
        for sc in data.service_centers:
            await self.session.execute(
                text("""
                    INSERT INTO service_centers (service_center_id, name, address, lat, lon, opening_hours, restock_duration_min)
                    VALUES (:id, :name, :addr, :lat, :lon, :oh, :rd)
                """),
                {"id": sc.service_center_id, "name": sc.name, "addr": sc.address, "lat": sc.lat, "lon": sc.lon, 
                 "oh": sc.opening_hours.model_dump_json(), "rd": sc.restock_duration_min}
            )
            
        for wt in data.work_types:
            await self.session.execute(
                text("""
                    INSERT INTO work_types (code, name, profiles, duration_min, max_start_delay_min, deadline_kind, deadline_value, repeat_deadline_value, pgp_relevant)
                    VALUES (:code, :name, :profiles, :dur, :msd, :dk, :dv, :rdv, :pgp)
                """),
                {"code": wt.code, "name": wt.name, "profiles": wt.profiles, "dur": wt.duration_min, 
                 "msd": wt.max_start_delay_min, "dk": wt.deadline_kind, "dv": wt.deadline_value, 
                 "rdv": wt.repeat_deadline_value, "pgp": wt.pgp_relevant}
            )

        for s in data.staff:
            await self.session.execute(
                text("""
                    INSERT INTO staff (staff_id, display_name, service_center_id, profiles, technologies, height_permit, shift, equipment_start, equipment_capacity, experience_years)
                    VALUES (:id, :name, :sc, :profiles, :techs, :height, :shift, :eq_start, :eq_cap, :exp)
                """),
                {"id": s.staff_id, "name": s.display_name, "sc": s.service_center_id, "profiles": s.profiles,
                 "techs": s.technologies, "height": s.height_permit, "shift": s.shift.model_dump_json(),
                 "eq_start": s.equipment_start.model_dump_json(), "eq_cap": s.equipment_capacity.model_dump_json(), "exp": s.experience_years}
            )

        for node in data.access_nodes:
            await self.session.execute(
                text("""
                    INSERT INTO access_nodes (access_node_id, node_type, technology, name, address, lat, lon)
                    VALUES (:id, :type, :tech, :name, :addr, :lat, :lon)
                """),
                {"id": node.access_node_id, "type": node.node_type, "tech": node.technology, "name": node.name, "addr": node.address, "lat": node.lat, "lon": node.lon}
            )
            for b in node.buildings:
                await self.session.execute(
                    text("""
                        INSERT INTO buildings (building_id, address, lat, lon, building_type, overhead_line, zone_service_center_id)
                        VALUES (:id, :addr, :lat, :lon, :type, :overhead, :zone)
                        ON CONFLICT (building_id) DO NOTHING
                    """),
                    {"id": b.building_id, "addr": b.address, "lat": b.lat, "lon": b.lon, "type": b.building_type, "overhead": b.overhead_line, "zone": b.zone_service_center_id}
                )
                await self.session.execute(
                    text("INSERT INTO access_node_buildings (access_node_id, building_id) VALUES (:node, :bldg) ON CONFLICT DO NOTHING"),
                    {"node": node.access_node_id, "bldg": b.building_id}
                )

        await self.session.commit()

    async def get_staff(self) -> list[Staff]:
        res = await self.session.execute(text("SELECT * FROM staff"))
        staff = []
        for row in res.mappings():
            d = dict(row)
            d["shift"] = _parse_json(d["shift"])
            d["equipment_start"] = _parse_json(d["equipment_start"])
            d["equipment_capacity"] = _parse_json(d["equipment_capacity"])
            staff.append(Staff(**d))
        return staff

    async def get_staff_by_id(self, staff_id: str) -> Staff | None:
        res = await self.session.execute(text("SELECT * FROM staff WHERE staff_id = :id"), {"id": staff_id})
        row = res.mappings().first()
        if row:
            d = dict(row)
            d["shift"] = _parse_json(d["shift"])
            d["equipment_start"] = _parse_json(d["equipment_start"])
            d["equipment_capacity"] = _parse_json(d["equipment_capacity"])
            return Staff(**d)
        return None

    async def get_work_types(self) -> list[WorkType]:
        res = await self.session.execute(text("SELECT * FROM work_types"))
        return [WorkType(**row) for row in res.mappings()]

    async def get_work_type_by_code(self, code: str) -> WorkType | None:
        res = await self.session.execute(text("SELECT * FROM work_types WHERE code = :code"), {"code": code})
        row = res.mappings().first()
        return WorkType(**row) if row else None

    async def get_service_centers(self) -> list[ServiceCenter]:
        res = await self.session.execute(text("SELECT * FROM service_centers"))
        centers = []
        for row in res.mappings():
            d = dict(row)
            d["opening_hours"] = _parse_json(d["opening_hours"])
            centers.append(ServiceCenter(**d))
        return centers

    async def get_access_nodes(self) -> list[AccessNode]:
        nodes_res = await self.session.execute(text("SELECT * FROM access_nodes"))
        nodes = []
        for node_row in nodes_res.mappings():
            node_dict = dict(node_row)
            bldg_res = await self.session.execute(text("""
                SELECT b.* FROM buildings b
                JOIN access_node_buildings ab ON b.building_id = ab.building_id
                WHERE ab.access_node_id = :nid
            """), {"nid": node_dict["access_node_id"]})
            node_dict["buildings"] = [Building(**b) for b in bldg_res.mappings()]
            nodes.append(AccessNode(**node_dict))
        return nodes