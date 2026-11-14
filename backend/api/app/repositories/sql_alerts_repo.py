from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.models import Alert
from datetime import datetime

class SqlAlertsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def append(self, date: str, alert: Alert) -> None:
        await self.session.execute(
            text("""
                INSERT INTO alerts (alert_id, date, created_at, type, status, resolved_at, order_id, group_id, staff_id, forecast_start, lateness_min, suggested_action, suggested_staff_id, proposed_slot, applied, message)
                VALUES (:aid, :d, :created, :type, :status, :resolved, :oid, :gid, :sid, :fstart, :late, :action, :s_sid, :p_slot, :applied, :msg)
            """),
            {"aid": alert.alert_id, "d": date, "created": alert.created_at, "type": alert.type, "status": alert.status,
             "resolved": alert.resolved_at, "oid": alert.order_id, "gid": alert.group_id, "sid": alert.staff_id,
             "fstart": alert.forecast_start, "late": alert.lateness_min, "action": alert.suggested_action,
             "s_sid": alert.suggested_staff_id, "p_slot": alert.proposed_slot.model_dump_json() if alert.proposed_slot else None,
             "applied": alert.applied, "msg": alert.message}
        )
        await self.session.commit()

    async def list_by_date(self, date: str) -> list[dict]:
        res = await self.session.execute(text("SELECT * FROM alerts WHERE date = :d"), {"d": date})
        return [dict(row) for row in res.mappings()]

    async def resolve(self, date: str, alert_id: str, resolved_at: datetime) -> None:
        await self.session.execute(text("UPDATE alerts SET status = 'RESOLVED', resolved_at = :r WHERE date = :d AND alert_id = :aid"), {"r": resolved_at, "d": date, "aid": alert_id})
        await self.session.commit()