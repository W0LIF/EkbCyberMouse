from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.models import DayInput

class SqlDayRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, day: DayInput) -> None:
        await self.session.execute(text("DELETE FROM days WHERE date = :d"), {"d": day.date})
        await self.session.execute(
            text("INSERT INTO days (date, model_now, absent_staff_ids, event_received) VALUES (:d, :now, :absent, FALSE)"),
            {"d": day.date, "now": day.now, "absent": day.absent_staff_ids}
        )
        await self.session.commit()

    async def get(self, date: str) -> dict | None:
        res = await self.session.execute(text("SELECT * FROM days WHERE date = :d"), {"d": date})
        row = res.mappings().first()
        return dict(row) if row else None

    async def mark_event_received(self, date: str) -> None:
        await self.session.execute(text("UPDATE days SET event_received = TRUE WHERE date = :d"), {"d": date})
        await self.session.commit()

    async def is_event_received(self, date: str) -> bool:
        res = await self.session.execute(text("SELECT event_received FROM days WHERE date = :d"), {"d": date})
        row = res.first()
        return row["event_received"] if row else False