from sqlalchemy import text
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from api.app.models import ReferenceData, Staff, ServiceCenter, AccessNode, WorkType
from api.app.repositories.db import AsyncSessionLocal
# Для SQLAlchemy нам нужны ORM-модели. Пока используем Core-подход через text() для простоты,
# но лучше создать orm.py. Для скорости напишем через Core-запросы.

class SqlReferenceRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def replace_all(self, data: ReferenceData) -> None:
        """Полностью заменяет справочники (вызывается при PUT /reference)."""
        # 1. Очищаем старые данные (каскадно затронет orders, так как там FK)
        await self.session.execute(text("TRUNCATE TABLE service_centers, staff, access_nodes, buildings, work_types CASCADE;"))
        
        # 2. Вставляем СЦ
        for sc in data.service_centers:
            await self.session.execute(
                text("""
                    INSERT INTO service_centers (service_center_id, name, address, lat, lon, opening_hours, restock_duration_min)
                    VALUES (:id, :name, :addr, :lat, :lon, :oh, :rd)
                """),
                {"id": sc.service_center_id, "name": sc.name, "addr": sc.address, "lat": sc.lat, "lon": sc.lon, 
                 "oh": sc.opening_hours.model_dump_json(), "rd": sc.restock_duration_min}
            )
            
        # 3. Вставляем WorkTypes
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

        # 4. Вставляем Staff
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

        # 5. Вставляем узлы и дома
        for node in data.access_nodes:
            await self.session.execute(
                text("""
                    INSERT INTO access_nodes (access_node_id, node_type, technology, name, address, lat, lon)
                    VALUES (:id, :type, :tech, :name, :addr, :lat, :lon)
                """),
                {"id": node.access_node_id, "type": node.node_type, "tech": node.technology, "name": node.name, "addr": node.address, "lat": node.lat, "lon": node.lon}
            )
            for b in node.buildings:
                # Используем ON CONFLICT, так как дом может быть в нескольких узлах
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
        # ... (остальные методы get_ можно дописать позже, для MVP достаточно загрузки)
        pass

    async def get_work_types(self) -> list[WorkType]:
        pass
        
    async def get_service_centers(self) -> list[ServiceCenter]:
        pass
        
    async def get_access_nodes(self) -> list[AccessNode]:
        pass