from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import MobileActionType


class SqlMobileRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_actions(
        self, date_value: date, staff_id: str
    ) -> dict[str, dict[str, datetime]]:
        result = await self.session.execute(
            text("""
                SELECT order_id, action, occurred_at
                FROM mobile_visit_actions
                WHERE date = :date AND staff_id = :staff_id
            """),
            {"date": date_value, "staff_id": staff_id},
        )
        actions: dict[str, dict[str, datetime]] = {}
        for row in result.mappings():
            actions.setdefault(row["order_id"], {})[row["action"]] = row[
                "occurred_at"
            ]
        return actions

    async def record_action(
        self,
        date_value: date,
        staff_id: str,
        order_id: str,
        action: MobileActionType,
        occurred_at: datetime,
    ) -> bool:
        result = await self.session.execute(
            text("""
                INSERT INTO mobile_visit_actions (
                    date, staff_id, order_id, action, occurred_at
                )
                VALUES (:date, :staff_id, :order_id, :action, :occurred_at)
                ON CONFLICT (date, staff_id, order_id, action) DO NOTHING
            """),
            {
                "date": date_value,
                "staff_id": staff_id,
                "order_id": order_id,
                "action": action,
                "occurred_at": occurred_at,
            },
        )
        return result.rowcount == 1
