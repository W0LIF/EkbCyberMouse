from __future__ import annotations
import time
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import (
    Alert, CancelledOrder, DayInput, Event, EventResult, Order, Plan, PlanSummary, PgpGroup, UnassignedOrder
)
from api.app.repositories.db import get_db
from api.app.repositories.sql_day_repo import SqlDayRepo
from api.app.repositories.sql_orders_repo import SqlOrdersRepo
from api.app.repositories.sql_plans_repo import SqlPlansRepo
from api.app.repositories.sql_reference_repo import SqlReferenceRepo
from api.app.repositories.sql_events_repo import SqlEventsRepo
from api.app.repositories.sql_alerts_repo import SqlAlertsRepo
from api.app.services.matrix_store import matrix_store
from solver.app.vrp import solve_vrp

router = APIRouter(tags=["events"])
_alert_counter: dict[str, int] = {}

def _next_alert_id(date: str) -> str:
    _alert_counter[date] = _alert_counter.get(date, 0) + 1
    return f"ALR-{date.replace('-', '')}-{_alert_counter[date]:04d}"

# (Функции _row_to_order_dict и _detect_pgp оставляем без изменений, они отличные!)
def _row_to_order_dict(row: dict) -> dict:
    def _iso(v):
        if v is None: return None
        if isinstance(v, datetime): return v.isoformat(timespec="seconds")
        return str(v)
    return {
        "order_id": row["order_id"], "work_type_code": row["work_type_code"], "technology": row["technology"],
        "building_id": row["building_id"], "address": row["address"], "lat": float(row["lat"]), "lon": float(row["lon"]),
        "building_type": row["building_type"], "requires_height": bool(row["requires_height"]),
        "access_node_id": row["access_node_id"], "registered_at": _iso(row["registered_at"]),
        "slot": {"start": _iso(row["slot_start"]), "end": _iso(row["slot_end"])},
        "latest_start": _iso(row["latest_start"]), "deadline": _iso(row["deadline"]),
        "required_equipment": {"ONT": int(row["req_ont"]), "ROUTER": int(row["req_router"]), "STB": int(row["req_stb"])},
        "is_repeat": bool(row["is_repeat"]), "previous_order_id": row.get("previous_order_id"),
    }

def _detect_pgp(orders_dicts: list[dict], work_types: list, now: datetime) -> list[PgpGroup]:
    pgp_codes = set()
    for wt in work_types:
        wt_dict = wt if isinstance(wt, dict) else wt.model_dump()
        if wt_dict.get("pgp_relevant"): pgp_codes.add(wt_dict["code"])

    node_orders = defaultdict(list)
    for o in orders_dicts:
        if o["work_type_code"] in pgp_codes and o.get("access_node_id"):
            node_orders[o["access_node_id"]].append(o)

    groups = []
    group_idx = 1
    for node_id, olist in node_orders.items():
        if len(olist) < 3: continue
        olist_sorted = sorted(olist, key=lambda x: x["registered_at"])
        i = 0
        while i < len(olist_sorted):
            window = []
            try: base_time = datetime.fromisoformat(olist_sorted[i]["registered_at"])
            except: i += 1; continue
            for j in range(i, len(olist_sorted)):
                try: t = datetime.fromisoformat(olist_sorted[j]["registered_at"])
                except: break
                if (t - base_time) <= timedelta(minutes=60): window.append(olist_sorted[j])
                else: break
            if len(window) >= 3:
                groups.append(PgpGroup(
                    group_id=f"PGP-{node_id}-{group_idx:02d}", access_node_id=node_id,
                    order_ids=[w["order_id"] for w in window], detected_at=now,
                    action="TRANSFER_TO_STATION", comment=f"ПГП на {node_id}: {len(window)} нарядов за 60 мин",
                ))
                group_idx += 1; i += len(window)
            else: i += 1
    return groups

@router.post("/days/{date}/events", response_model=EventResult)
async def post_event(date: str, event: Event, db: AsyncSession = Depends(get_db)):
    t0 = time.time()
    day_repo = SqlDayRepo(db); orders_repo = SqlOrdersRepo(db); plans_repo = SqlPlansRepo(db)
    events_repo = SqlEventsRepo(db); alerts_repo = SqlAlertsRepo(db); ref_repo = SqlReferenceRepo(db)

    # 1. Проверки данных
    day_row = await day_repo.get(date)
    if not day_row: raise HTTPException(404, f"День {date} не загружен")
    staff = await ref_repo.get_staff(); work_types = await ref_repo.get_work_types()
    service_centers = await ref_repo.get_service_centers()
    if not staff or not work_types: raise HTTPException(400, "Справочники не загружены")
    if not matrix_store.is_loaded(): raise HTTPException(400, "Матрица не загружена")
    
    plan_data = await plans_repo.get_latest(date)
    if not plan_data: raise HTTPException(404, f"План на {date} ещё не построен")

    # 2. Идемпотентность и порядок
    if await events_repo.get_by_event_id(date, event.event_id):
        return EventResult(event_id=event.event_id, accepted=True, duplicate=True, plan_version=plan_data.get("plan_version", 1), as_of=plan_data.get("as_of"), message="Дубликат")
    last_ts = await events_repo.get_last_timestamp(date)
    if last_ts and event.timestamp < last_ts: raise HTTPException(409, "timestamp раньше последнего события")

    # 3. Загрузка нарядов
    orders_raw = await orders_repo.get_by_date(date)
    orders_dicts = [_row_to_order_dict(r) for r in orders_raw]
    
    # Обработка новых/отмененных нарядов
    if event.type == "NEW_ORDER":
        await orders_repo.upsert_many(date, [event.order])
        orders_raw = await orders_repo.get_by_date(date)
        orders_dicts = [_row_to_order_dict(r) for r in orders_raw]
    
    cancelled_ids = {c["order_id"] for c in plan_data.get("cancelled", [])}
    if event.type == "ORDER_CANCELLED": cancelled_ids.add(event.order_id)
        
    unavailable_staff_ids = {r["staff_id"] for r in plan_data.get("routes", []) if r.get("status") == "UNAVAILABLE"}
    if event.type == "STAFF_UNAVAILABLE": unavailable_staff_ids.add(event.staff_id)

    # 4. ПГП
    active_orders = [o for o in orders_dicts if o["order_id"] not in cancelled_ids]
    pgp_groups = _detect_pgp(active_orders, work_types, event.timestamp)
    pgp_order_ids = {oid for g in pgp_groups for oid in g.order_ids}
    
    # 5. ЗАМОРОЗКА (H10) - самое важное!
    # Находим визиты, которые УЖЕ начались (start < now), и убираем их из солвера.
    # Солвер должен распределять только НЕ начатые наряды.
    frozen_order_ids = set()
    for route in plan_data.get("routes", []):
        for stop in route.get("stops", []):
            if stop.get("type") == "VISIT" and stop.get("start"):
                if datetime.fromisoformat(stop["start"]) < event.timestamp:
                    frozen_order_ids.add(stop["order_id"])
    
    orders_for_solver = [
        o for o in active_orders 
        if o["order_id"] not in pgp_order_ids and o["order_id"] not in frozen_order_ids
    ]

    # 6. Вызов СОЛВЕРА (исправлена сигнатура!)
    # Формируем DayInput
    day_input = DayInput(date=date, now=day_row["model_now"], orders=[Order(**o) for o in orders_for_solver], absent_staff_ids=day_row["absent_staff_ids"] or [])
    
    if orders_for_solver:
        try:
            # Ограничиваем время солвера 3 секундами, чтобы уложиться в SLA
            new_plan = solve_vrp(day_input, staff, matrix_store.as_matrix(), work_types)
        except Exception as e:
            new_plan = Plan(date=date, plan_version=plan_data.get("plan_version", 1)+1, as_of=event.timestamp, routes=[], unassigned=[], pgp_groups=[], cancelled=[], alerts=[])
    else:
        new_plan = Plan(date=date, plan_version=plan_data.get("plan_version", 1)+1, as_of=event.timestamp, routes=[], unassigned=[], pgp_groups=[], cancelled=[], alerts=[])

    # 7. Мержим замороженные визиты обратно в план (они должны остаться на своих местах)
    for route_data in plan_data.get("routes", []):
        new_route = next((r for r in new_plan.routes if r.staff_id == route_data["staff_id"]), None)
        if new_route:
            for stop_data in route_data.get("stops", []):
                if stop_data.get("order_id") in frozen_order_ids:
                    # Возвращаем замороженный визит в маршрут
                    from api.app.models import Stop
                    new_route.stops.append(Stop(**stop_data))
            # Сортируем по seq
            new_route.stops.sort(key=lambda x: x.seq)

    # 8. Обновляем ПГП и отмены
    new_plan.pgp_groups = pgp_groups
    new_plan.cancelled = [CancelledOrder(order_id=oid, cancelled_at=event.timestamp) for oid in cancelled_ids]
    new_plan.based_on_event_id = event.event_id

    # 9. Алерты (упрощенно)
    new_alerts = []
    for u in new_plan.unassigned:
        new_alerts.append(Alert(
            alert_id=_next_alert_id(date), created_at=event.timestamp, type="UNASSIGNED",
            status="ACTIVE", order_id=u.order_id, suggested_action="ESCALATE", applied=False, message="Не назначен"
        ))
    new_plan.alerts = new_alerts

    # 10. Сохранение в БД
    processing_ms = int((time.time() - t0) * 1000)
    new_plan.computation_ms = processing_ms
    
    await events_repo.append(date, event, event.timestamp, processing_ms)
    await plans_repo.save_version(date, new_plan)
    await day_repo.mark_event_received(date)
    for alert in new_alerts: await alerts_repo.append(date, alert)

    return EventResult(
        event_id=event.event_id, accepted=True, duplicate=False,
        plan_version=new_plan.plan_version, as_of=event.timestamp,
        processing_ms=processing_ms, message=f"Событие {event.type} обработано"
    )