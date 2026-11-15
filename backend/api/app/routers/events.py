from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from api.app.models import (
    Alert,
    CancelledOrder,
    DayInput,
    Event,
    EventResult,
    NewOrderEvent,
    OrderCancelledEvent,
    Order,
    OrderTransferredEvent,
    Plan,
    PlanSummary,
    Route,
    StaffUnavailableEvent,
    UnassignedOrder,
    VisitDelayedEvent,
)
from api.app.repositories.db import get_db
from api.app.repositories.sql_alerts_repo import SqlAlertsRepo
from api.app.repositories.sql_day_repo import SqlDayRepo
from api.app.repositories.sql_events_repo import SqlEventsRepo
from api.app.repositories.sql_orders_repo import SqlOrdersRepo
from api.app.repositories.sql_plans_repo import SqlPlansRepo
from api.app.repositories.sql_reference_repo import SqlReferenceRepo
from api.app.services.matrix_store import matrix_store
from api.app.services.pgp import detect_pgp_groups
from api.app.services.alerts import (
    generate_late_risk_alerts,
    generate_new_pgp_alerts,
)
from api.app.services.duration_forecast import apply_duration_forecasts
from solver.app.vrp import solve_vrp

router = APIRouter(tags=["events"])


def _row_to_order_dict(row: dict) -> dict:
    def iso(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat(timespec="seconds")
        return str(value)

    return {
        "order_id": row["order_id"],
        "work_type_code": row["work_type_code"],
        "technology": row["technology"],
        "building_id": row["building_id"],
        "address": row["address"],
        "lat": float(row["lat"]),
        "lon": float(row["lon"]),
        "building_type": row["building_type"],
        "requires_height": bool(row["requires_height"]),
        "access_node_id": row["access_node_id"],
        "registered_at": iso(row["registered_at"]),
        "slot": {"start": iso(row["slot_start"]), "end": iso(row["slot_end"])},
        "latest_start": iso(row["latest_start"]),
        "deadline": iso(row["deadline"]),
        "required_equipment": {
            "ONT": int(row["req_ont"]),
            "ROUTER": int(row["req_router"]),
            "STB": int(row["req_stb"]),
        },
        "is_repeat": bool(row["is_repeat"]),
        "previous_order_id": row.get("previous_order_id"),
    }


def _recalculate_after(
    route: dict, stop_index: int, event_timestamp: datetime
) -> None:
    stops = route["stops"]
    for index in range(stop_index + 1, len(stops)):
        previous, current = stops[index - 1], stops[index]
        previous_end = datetime.fromisoformat(previous["end"])
        departure_time = max(previous_end, event_timestamp)
        travel_sec, distance_m = matrix_store.get(
            previous["location_id"],
            current["location_id"],
            departure_time,
        )
        old_arrival = datetime.fromisoformat(current["arrival"])
        old_start = datetime.fromisoformat(current["start"])
        old_end = datetime.fromisoformat(current["end"])
        duration = old_end - old_start
        arrival = max(
            old_arrival,
            max(previous_end, event_timestamp) + timedelta(seconds=travel_sec),
        )
        start = max(old_start, arrival)
        current["travel_sec"] = travel_sec
        current["distance_m"] = distance_m
        current["arrival"] = arrival.isoformat(timespec="seconds")
        current["start"] = start.isoformat(timespec="seconds")
        current["end"] = (start + duration).isoformat(timespec="seconds")


def _frozen_stops(route: dict, event_timestamp: datetime) -> list[dict]:
    return [
        stop
        for stop in route["stops"]
        if stop.get("status") in {"IN_PROGRESS", "DONE"}
        or datetime.fromisoformat(stop["start"]) < event_timestamp
    ]


@router.post("/days/{date}/events", response_model=EventResult)
async def post_event(
    date: str,
    event: Event,
    db: AsyncSession = Depends(get_db),
):
    started = time.monotonic()
    day_repo = SqlDayRepo(db)
    orders_repo = SqlOrdersRepo(db)
    plans_repo = SqlPlansRepo(db)
    events_repo = SqlEventsRepo(db)
    alerts_repo = SqlAlertsRepo(db)
    reference_repo = SqlReferenceRepo(db)

    day_row = await day_repo.get(date)
    if not day_row:
        raise HTTPException(404, f"День {date} не загружен")
    plan_data = await plans_repo.get_latest(date)
    if not plan_data:
        raise HTTPException(404, f"План на {date} ещё не построен")
    if not matrix_store.is_loaded():
        raise HTTPException(400, "Матрица не загружена")

    if await events_repo.get_by_event_id(date, event.event_id):
        return EventResult(
            event_id=event.event_id,
            accepted=True,
            duplicate=True,
            plan_version=plan_data["plan_version"],
            as_of=plan_data["as_of"],
            message="Дубликат события",
        )

    last_timestamp = await events_repo.get_last_timestamp(date)
    if last_timestamp and event.timestamp < last_timestamp:
        raise HTTPException(409, "timestamp раньше последнего события")

    staff = await reference_repo.get_staff()
    work_types = await reference_repo.get_work_types()
    centers = await reference_repo.get_service_centers()
    staff_ids = {person.staff_id for person in staff}
    if not staff or not work_types or not centers:
        raise HTTPException(400, "Справочники не загружены")

    all_orders = [
        _row_to_order_dict(row) for row in await orders_repo.get_by_date(date)
    ]
    if isinstance(event, NewOrderEvent):
        expected_prefix = f"ORD-{date.replace('-', '')}-"
        if not event.order.order_id.startswith(expected_prefix):
            raise HTTPException(422, "order_id не соответствует дате события")
        if any(item["order_id"] == event.order.order_id for item in all_orders):
            raise HTTPException(422, f"Наряд {event.order.order_id} уже существует")
        all_orders.append(event.order.model_dump(mode="json"))

    order_ids = {item["order_id"] for item in all_orders}
    if isinstance(event, OrderCancelledEvent) and event.order_id not in order_ids:
        raise HTTPException(422, f"Наряд {event.order_id} не найден")
    if isinstance(event, (VisitDelayedEvent, OrderTransferredEvent)):
        if event.staff_id not in staff_ids:
            raise HTTPException(422, f"Сотрудник {event.staff_id} не найден")
        matching = [
            (route, stop)
            for route in plan_data["routes"]
            for stop in route["stops"]
            if stop.get("order_id") == event.order_id
            and route["staff_id"] == event.staff_id
            and stop["type"] == "VISIT"
        ]
        if not matching:
            raise HTTPException(422, "Визит сотрудника не найден в текущем плане")
        route, stop = matching[0]
        if datetime.fromisoformat(stop["start"]) >= event.timestamp:
            raise HTTPException(422, "Событие относится к ещё не начатому визиту")
        if isinstance(event, VisitDelayedEvent):
            end_time = event.expected_end
        else:
            end_time = event.actual_end
        stop["end"] = end_time.isoformat(timespec="seconds")
        _recalculate_after(route, route["stops"].index(stop), event.timestamp)
    if isinstance(event, StaffUnavailableEvent) and event.staff_id not in staff_ids:
        raise HTTPException(422, f"Сотрудник {event.staff_id} не найден")

    cancelled_ids = {item["order_id"] for item in plan_data.get("cancelled", [])}
    if isinstance(event, OrderCancelledEvent):
        if any(
            stop.get("order_id") == event.order_id
            and datetime.fromisoformat(stop["start"]) < event.timestamp
            for route in plan_data["routes"]
            for stop in route["stops"]
        ):
            raise HTTPException(422, "Нельзя отменить уже начатый визит")
        cancelled_ids.add(event.order_id)

    frozen_order_ids = {
        stop["order_id"]
        for route in plan_data["routes"]
        for stop in route["stops"]
        if stop["type"] == "VISIT"
        and stop.get("order_id")
        and datetime.fromisoformat(stop["start"]) < event.timestamp
    }
    active_orders = [
        order for order in all_orders if order["order_id"] not in cancelled_ids
    ]
    pgp_groups = detect_pgp_groups(
        [
            order
            for order in active_orders
            if order["order_id"] not in frozen_order_ids
        ],
        work_types,
        event.timestamp,
    )
    pgp_order_ids = {order_id for group in pgp_groups for order_id in group.order_ids}

    unavailable_staff_ids = {
        route["staff_id"]
        for route in plan_data["routes"]
        if route.get("status") == "UNAVAILABLE"
        and (
            not route.get("unavailable_until")
            or datetime.fromisoformat(route["unavailable_until"]) > event.timestamp
        )
    }
    if isinstance(event, StaffUnavailableEvent):
        unavailable_staff_ids.add(event.staff_id)

    retained_routes = []
    retained_order_ids = set()
    for route_data in plan_data["routes"]:
        route_staff_ids = {
            route_data["staff_id"],
            *(route_data.get("team_staff_ids") or []),
        }
        is_unavailable = bool(route_staff_ids & unavailable_staff_ids)
        was_temporarily_unavailable = (
            route_data.get("status") == "UNAVAILABLE"
            and route_data.get("unavailable_until") is not None
            and datetime.fromisoformat(route_data["unavailable_until"])
            <= event.timestamp
        )
        frozen_stops = _frozen_stops(route_data, event.timestamp)
        if not frozen_stops and not is_unavailable:
            continue

        original_stops = list(route_data["stops"])
        route_data = {
            **route_data,
            "stops": frozen_stops,
        }
        if is_unavailable:
            route_data["status"] = "UNAVAILABLE"
            route_data["unavailable_from"] = event.timestamp.isoformat(
                timespec="seconds"
            )
            unavailable_until = (
                event.until
                if isinstance(event, StaffUnavailableEvent)
                and event.staff_id in route_staff_ids
                else None
            )
            route_data["unavailable_until"] = (
                unavailable_until.isoformat(timespec="seconds")
                if unavailable_until
                else route_data.get("unavailable_until")
            )
            route_data["stops"] = [
                stop for stop in route_data["stops"] if stop["type"] != "DEPOT_END"
            ]
        else:
            if was_temporarily_unavailable:
                route_data["status"] = "ACTIVE"
                route_data["unavailable_from"] = None
                route_data["unavailable_until"] = None
            depot_end = next(
                (stop for stop in original_stops if stop["type"] == "DEPOT_END"),
                None,
            )
            if depot_end is not None:
                route_data["stops"].append(depot_end)
                _recalculate_after(
                    route_data,
                    len(route_data["stops"]) - 2,
                    event.timestamp,
                )
            elif was_temporarily_unavailable and route_data["stops"]:
                previous = route_data["stops"][-1]
                travel_sec, distance_m = matrix_store.get(
                    previous["location_id"],
                    route_data["service_center_id"],
                    max(datetime.fromisoformat(previous["end"]), event.timestamp),
                )
                depot_arrival = max(
                    datetime.fromisoformat(previous["end"]),
                    event.timestamp,
                ) + timedelta(seconds=travel_sec)
                route_data["stops"].append(
                    {
                        "seq": len(route_data["stops"]) + 1,
                        "type": "DEPOT_END",
                        "location_id": route_data["service_center_id"],
                        "arrival": depot_arrival.isoformat(timespec="seconds"),
                        "start": depot_arrival.isoformat(timespec="seconds"),
                        "end": depot_arrival.isoformat(timespec="seconds"),
                        "travel_sec": travel_sec,
                        "distance_m": distance_m,
                        "equipment_after": previous.get("equipment_after"),
                    }
                )
        route_data["stops"] = [
            stop
            for stop in route_data["stops"]
            if stop.get("order_id") not in cancelled_ids
            and stop.get("order_id") not in pgp_order_ids
        ]
        for sequence, stop in enumerate(route_data["stops"], start=1):
            stop["seq"] = sequence
            if stop.get("order_id") and stop["type"] == "VISIT":
                retained_order_ids.add(stop["order_id"])
        totals = route_data.get("totals") or {}
        visit_stops = [
            stop for stop in route_data["stops"] if stop["type"] == "VISIT"
        ]
        totals.update(
            visits=len(visit_stops),
            travel_sec=sum(stop.get("travel_sec") or 0 for stop in route_data["stops"]),
            distance_m=sum(stop.get("distance_m") or 0 for stop in route_data["stops"]),
            work_min=sum(
                int(
                    (
                        datetime.fromisoformat(stop["end"])
                        - datetime.fromisoformat(stop["start"])
                    ).total_seconds()
                    // 60
                )
                for stop in visit_stops
            ),
        )
        route_data["totals"] = totals
        retained_routes.append(Route.model_validate(route_data))

    solver_orders = [
        order
        for order in active_orders
        if order["order_id"] not in frozen_order_ids
        and order["order_id"] not in pgp_order_ids
        and order["order_id"] not in retained_order_ids
    ]
    apply_duration_forecasts(
        solver_orders,
        await orders_repo.get_duration_history(),
        [work_type.model_dump() for work_type in work_types],
    )
    retained_staff_ids = {
        staff_id
        for route in retained_routes
        for staff_id in [route.staff_id, *(route.team_staff_ids or [])]
    }
    solver_staff = [
        person
        for person in staff
        if person.staff_id not in unavailable_staff_ids
        and person.staff_id not in retained_staff_ids
    ]
    event_day = DayInput(
        date=date,
        now=event.timestamp,
        orders=[Order.model_validate(order) for order in solver_orders],
        absent_staff_ids=sorted(unavailable_staff_ids),
    )

    if solver_orders and solver_staff:
        new_plan = await run_in_threadpool(
            solve_vrp,
            date=date,
            day=event_day,
            orders=solver_orders,
            staff=solver_staff,
            work_types=work_types,
            service_centers=centers,
            matrix=matrix_store.as_matrix(),
            plan_version=plan_data["plan_version"] + 1,
            max_runtime_seconds=8,
        )
    else:
        new_plan = Plan(
            date=date,
            plan_version=plan_data["plan_version"] + 1,
            as_of=event.timestamp,
            routes=[],
            unassigned=[],
            pgp_groups=[],
            cancelled=[],
            alerts=[],
        )

    new_plan.routes = retained_routes + new_plan.routes
    new_plan.pgp_groups = pgp_groups
    new_plan.cancelled = [
        CancelledOrder(
            order_id=order_id,
            cancelled_at=event.timestamp,
            event_id=(
                event.event_id
                if isinstance(event, OrderCancelledEvent)
                and order_id == event.order_id
                else None
            ),
        )
        for order_id in sorted(cancelled_ids)
    ]
    new_plan.based_on_event_id = event.event_id
    new_plan.as_of = event.timestamp

    known_elsewhere = (
        frozen_order_ids | retained_order_ids | pgp_order_ids | cancelled_ids
    )
    missing_orders = [
        order
        for order in active_orders
        if order["order_id"] not in known_elsewhere
        and order["order_id"]
        not in {item.order_id for item in new_plan.unassigned}
        and order["order_id"]
        not in {
            stop.order_id
            for route in new_plan.routes
            for stop in route.stops
            if stop.type == "VISIT"
        }
    ]
    for order in missing_orders:
        new_plan.unassigned.append(
            UnassignedOrder(
                order_id=order["order_id"],
                reason_code="OTHER",
                reason_text="Не удалось назначить после события",
                suggested_action="ESCALATE",
            )
        )

    old_alerts = [Alert.model_validate(item) for item in plan_data.get("alerts", [])]
    new_alerts = [
        Alert(
            alert_id=f"ALR-{date.replace('-', '')}-{uuid.uuid4().hex[:12]}",
            created_at=event.timestamp,
            type="UNASSIGNED",
            status="ACTIVE",
            order_id=item.order_id,
            suggested_action=(
                item.suggested_action
                if item.suggested_action in ("REASSIGN", "RESCHEDULE")
                else "NONE"
            ),
            applied=False,
            message=f"Наряд {item.order_id} не распределен: {item.reason_text}",
        )
        for item in new_plan.unassigned
    ]
    new_alerts.extend(
        generate_new_pgp_alerts(
            pgp_groups,
            plan_data.get("pgp_groups", []),
            event.timestamp,
        )
    )
    existing_late_risk_orders = {
        alert.order_id
        for alert in old_alerts
        if alert.type == "LATE_RISK" and alert.status == "ACTIVE"
    }
    new_alerts.extend(
        alert
        for alert in generate_late_risk_alerts(
            new_plan,
            {order["order_id"]: order for order in all_orders},
            event.timestamp,
        )
        if alert.order_id not in existing_late_risk_orders
    )
    new_plan.alerts = old_alerts + new_alerts
    new_plan.summary = PlanSummary(
        orders_total=len(all_orders),
        visits_planned=len({
            stop.order_id
            for route in new_plan.routes
            for stop in route.stops
            if stop.type == "VISIT" and stop.order_id
        }),
        unassigned=len(new_plan.unassigned),
        pgp_orders=len(pgp_order_ids),
        cancelled=len(cancelled_ids),
        travel_sec_total=sum(
            route.totals.travel_sec or 0
            for route in new_plan.routes
            if route.totals
        ),
    )
    processing_ms = int((time.monotonic() - started) * 1000)
    new_plan.computation_ms = processing_ms

    if isinstance(event, NewOrderEvent):
        await orders_repo.upsert_many(
            date,
            [event.order],
            replace_existing=False,
            commit=False,
        )
    await events_repo.append(
        date, event, event.timestamp, processing_ms, commit=False
    )
    await plans_repo.save_version(date, new_plan, commit=False)
    await day_repo.update_model_now(date, event.timestamp, commit=False)
    await day_repo.mark_event_received(date, commit=False)
    for alert in new_alerts:
        await alerts_repo.append(date, alert, commit=False)
    await db.commit()

    return EventResult(
        event_id=event.event_id,
        accepted=True,
        duplicate=False,
        plan_version=new_plan.plan_version,
        as_of=event.timestamp,
        processing_ms=processing_ms,
        changed_staff_ids=sorted({
            staff_id
            for route in new_plan.routes
            for staff_id in [route.staff_id, *(route.team_staff_ids or [])]
        }),
        new_alerts=new_alerts,
        message=f"Событие {event.type} обработано",
    )
