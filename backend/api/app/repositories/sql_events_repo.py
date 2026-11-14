from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.models import Event
from datetime import datetime

class SqlEventsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _parse_date(self, date_str: str):
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    async def append(self, date: str, event: Event, processed_at: datetime, response_ms: int) -> None:
        d = self._parse_date(date)
        await self.session.execute(
            text("""
                INSERT INTO events (date, event_id, type, timestamp, payload, processed_at, response_ms)
                VALUES (:d, :eid, :type, :ts, :payload, :proc_at, :resp_ms)
            """),
            {"d": d, "eid": event.event_id, "type": event.type, "ts": event.timestamp, 
             "payload": event.model_dump_json(), "proc_at": processed_at, "resp_ms": response_ms}
        )
        await self.session.commit()

    async def get_by_event_id(self, date: str, event_id: str) -> dict | None:
        d = self._parse_date(date)
        res = await self.session.execute(text("SELECT * FROM events WHERE date = :d AND event_id = :eid"), {"d": d, "eid": event_id})
        row = res.mappings().first()
        return dict(row) if row else None

    async def get_last_timestamp(self, date: str) -> datetime | None:
        d = self._parse_date(date)
        res = await self.session.execute(text("SELECT MAX(timestamp) as ts FROM events WHERE date = :d"), {"d": d})
        row = res.first()
        return row["ts"] if row and row["ts"] else None