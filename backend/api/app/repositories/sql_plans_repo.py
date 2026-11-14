from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from api.app.models import Plan
import json

class SqlPlansRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_version(self, date: str, plan: Plan):
        """Сохраняет план в БД через сырой SQL."""
        # Превращаем строку "2026-10-26" в объект datetime.date
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Превращаем Pydantic-модель в JSON-строку
        plan_json = plan.model_dump_json()
        
        # Сначала проверяем, есть ли уже такая версия
        check_sql = text("""
            SELECT id FROM plan_versions 
            WHERE date = :date AND version = :version
        """)
        result = await self.session.execute(check_sql, {"date": date_obj, "version": plan.plan_version})
        existing = result.scalar_one_or_none()
        
        if existing:
            # Если версия есть, обновляем её
            update_sql = text("""
                UPDATE plan_versions 
                SET payload = :payload, as_of = :as_of, based_on_event_id = :based_on
                WHERE id = :id
            """)
            await self.session.execute(update_sql, {
                "payload": plan_json,
                "as_of": plan.as_of,
                "based_on": plan.based_on_event_id,
                "id": existing
            })
        else:
            # Если нет, создаём новую
            insert_sql = text("""
                INSERT INTO plan_versions (date, version, based_on_event_id, as_of, payload, computed_ms)
                VALUES (:date, :version, :based_on, :as_of, :payload, :computed_ms)
            """)
            await self.session.execute(insert_sql, {
                "date": date_obj,
                "version": plan.plan_version,
                "based_on": plan.based_on_event_id,
                "as_of": plan.as_of,
                "payload": plan_json,
                "computed_ms": plan.computation_ms
            })
            
        await self.session.commit()

    async def get_latest(self, date: str) -> Plan | None:
        """Возвращает последнюю версию плана."""
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        
        sql = text("""
            SELECT payload FROM plan_versions 
            WHERE date = :date 
            ORDER BY version DESC 
            LIMIT 1
        """)
        result = await self.session.execute(sql, {"date": date_obj})
        row = result.fetchone()
        
        if row:
            # Если в БД payload хранится как строка JSON, то парсим
            payload_data = row[0]
            if isinstance(payload_data, str):
                payload_data = json.loads(payload_data)
            return Plan.model_validate(payload_data)
        return None