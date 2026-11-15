from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.models import Plan
from datetime import datetime
import json

class SqlPlansRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _parse_date(self, date_str: str):
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    async def save_version(
        self, date: str, plan: Plan, *, commit: bool = True
    ) -> None:
        d = self._parse_date(date)
        await self.session.execute(
            text("""
                INSERT INTO plan_versions (date, version, based_on_event_id, as_of, payload, computed_ms)
                VALUES (:d, :v, :evid, :as_of, :payload, :ms)
                ON CONFLICT (date, version) DO UPDATE
                SET based_on_event_id = :evid, as_of = :as_of, payload = :payload, computed_ms = :ms
            """),
            {"d": d, "v": plan.plan_version, "evid": plan.based_on_event_id, 
             "as_of": plan.as_of, "payload": plan.model_dump_json(), "ms": plan.computation_ms}
        )
        if commit:
            await self.session.commit()

    async def get_latest(self, date: str) -> dict | None:
        d = self._parse_date(date)
        res = await self.session.execute(text("SELECT payload FROM plan_versions WHERE date = :d ORDER BY version DESC LIMIT 1"), {"d": d})
        row = res.mappings().first()
        if not row:
            return None
        payload = row["payload"]
        if isinstance(payload, str):
            return json.loads(payload)
        return payload

    async def get_version(self, date: str, version: int) -> dict | None:
        d = self._parse_date(date)
        res = await self.session.execute(text("SELECT payload FROM plan_versions WHERE date = :d AND version = :v"), {"d": d, "v": version})
        row = res.mappings().first()
        if not row:
            return None
        payload = row["payload"]
        if isinstance(payload, str):
            return json.loads(payload)
        return payload

    async def delete_date(self, date: str) -> None:
        d = self._parse_date(date)
        await self.session.execute(text("DELETE FROM plan_versions WHERE date = :d"), {"d": d})
        await self.session.commit()