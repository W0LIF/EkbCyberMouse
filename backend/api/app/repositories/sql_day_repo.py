from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.models import DayInput
from datetime import datetime

class SqlDayRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _parse_date(self, date_str: str):
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    async def upsert(self, day: DayInput) -> None:
        d = self._parse_date(day.date)
        # Удаляем связанные записи (FK constraints)
        await self.session.execute(text("DELETE FROM alerts WHERE date = :d"), {"d": d})
        await self.session.execute(text("DELETE FROM events WHERE date = :d"), {"d": d})
        await self.session.execute(text("DELETE FROM plan_versions WHERE date = :d"), {"d": d})
        await self.session.execute(text("DELETE FROM days WHERE date = :d"), {"d": d})
        await self.session.execute(
            text("INSERT INTO days (date, model_now, absent_staff_ids, event_received) VALUES (:d, :now, :absent, FALSE)"),
            {"d": d, "now": day.now, "absent": day.absent_staff_ids}
        )
        await self.session.commit()

    async def get(self, date: str) -> dict | None:
        d = self._parse_date(date)
        res = await self.session.execute(text("SELECT * FROM days WHERE date = :d"), {"d": d})
        row = res.mappings().first()
        return dict(row) if row else None

    async def mark_event_received(self, date: str) -> None:
        d = self._parse_date(date)
        await self.session.execute(text("UPDATE days SET event_received = TRUE WHERE date = :d"), {"d": d})
        await self.session.commit()

    async def is_event_received(self, date: str) -> bool:
        d = self._parse_date(date)
        res = await self.session.execute(text("SELECT event_received FROM days WHERE date = :d"), {"d": d})
        row = res.first()
        return row["event_received"] if row else False

    async def delete_date(self, date: str) -> None:
        """Удалить день (для сброса при PUT /days/{date})."""
        d = self._parse_date(date)
        await self.session.execute(text("DELETE FROM days WHERE date = :d"), {"d": d})
        await self.session.commit()