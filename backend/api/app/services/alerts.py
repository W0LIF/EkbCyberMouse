import uuid
from datetime import datetime
from api.app.models import Alert, UnassignedOrder, PgpGroup

def generate_unassigned_alert(order: UnassignedOrder, now: datetime) -> Alert:
    """Создает алерт для наряда, который не удалось распределить."""
    return Alert(
        alert_id=f"ALR-{uuid.uuid4().hex[:8]}",
        created_at=now,
        type="UNASSIGNED",
        status="ACTIVE",
        order_id=order.order_id,
        suggested_action=order.suggested_action,
        message=f"Наряд {order.order_id} не распределен. Причина: {order.reason_text}",
        applied=False
    )

def generate_pgp_alert(group: PgpGroup, now: datetime) -> Alert:
    """Создает алерт при обнаружении групповой проблемы (ПГП)."""
    return Alert(
        alert_id=f"ALR-{uuid.uuid4().hex[:8]}",
        created_at=now,
        type="PGP_DETECTED",
        status="ACTIVE",
        group_id=group.group_id,
        suggested_action="TRANSFER_TO_STATION",
        message=f"Обнаружена ПГП на узле {group.access_node_id}. Наряды: {len(group.order_ids)} шт. Передано в станционное подразделение.",
        applied=True # Сразу применяем, так как мы их уже исключили из солвера
    )


def generate_new_pgp_alerts(
    groups: list[PgpGroup],
    previous_groups: list[dict],
    now: datetime,
) -> list[Alert]:
    previous_compositions = {
        tuple(sorted(group.get("order_ids", []))) for group in previous_groups
    }
    return [
        generate_pgp_alert(group, now)
        for group in groups
        if tuple(sorted(group.order_ids)) not in previous_compositions
    ]


def generate_late_risk_alerts(plan, orders_dict: dict, now: datetime) -> list[Alert]:
    """
    Создает предупреждения для визитов, прогнозируемое начало которых позже latest_start.
    """
    alerts = []
    
    for route in plan.routes:
        for stop in route.stops:
            if stop.type == "VISIT" and stop.order_id:
                order = orders_dict.get(stop.order_id)
                if not order:
                    continue
                
                latest_start = order["latest_start"]
                if isinstance(latest_start, str):
                    latest_start = datetime.fromisoformat(latest_start)
                if stop.start > now and stop.start > latest_start:
                    lateness_min = int((stop.start - latest_start).total_seconds() / 60)
                    
                    alert = Alert(
                        alert_id=f"ALR-{uuid.uuid4().hex[:8]}",
                        created_at=now,
                        type="LATE_RISK",
                        status="ACTIVE",
                        order_id=stop.order_id,
                        staff_id=route.staff_id,
                        forecast_start=stop.start,
                        lateness_min=lateness_min,
                        suggested_action="REASSIGN",
                        message=f"Сотрудник {route.staff_id} опаздывает на {lateness_min} мин по наряду {stop.order_id}",
                        applied=False
                    )
                    alerts.append(alert)
                    
    return alerts