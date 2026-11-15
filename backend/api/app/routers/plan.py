from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
import time
from datetime import date as date_class, datetime
import logging

logger = logging.getLogger(__name__)

from api.app.models import (
    DayInput,
    LoadResult,
    Order,
    Plan,
    PlanRequest,
    PlanSummary,
    ScenarioMetrics,
    ScenarioRequest,
    ScenarioResponse,
    Staff,
)
from api.app.services.matrix_store import matrix_store
from api.app.services.pgp import detect_pgp_groups
from api.app.services.alerts import (
    generate_late_risk_alerts,
    generate_pgp_alert,
)
from api.app.services.duration_forecast import apply_duration_forecasts
from api.app.repositories.db import get_db
from api.app.repositories.sql_day_repo import SqlDayRepo
from api.app.repositories.sql_orders_repo import SqlOrdersRepo
from api.app.repositories.sql_plans_repo import SqlPlansRepo
from api.app.repositories.sql_reference_repo import SqlReferenceRepo
from api.app.repositories.sql_events_repo import SqlEventsRepo
from solver.app.vrp import solve_vrp

router = APIRouter(tags=["plan"])


def _flat_to_order(row: dict) -> dict:
    """Превращает плоскую строку из БД в структуру, понятную solver-у."""
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
        "registered_at": row["registered_at"].isoformat() if isinstance(row["registered_at"], datetime) else row["registered_at"],
        "slot": {
            "start": row["slot_start"].isoformat() if isinstance(row["slot_start"], datetime) else row["slot_start"],
            "end": row["slot_end"].isoformat() if isinstance(row["slot_end"], datetime) else row["slot_end"],
        },
        "latest_start": row["latest_start"].isoformat() if isinstance(row["latest_start"], datetime) else row["latest_start"],
        "deadline": row["deadline"].isoformat() if isinstance(row["deadline"], datetime) else row["deadline"],
        "required_equipment": {
            "ONT": int(row["req_ont"]),
            "ROUTER": int(row["req_router"]),
            "STB": int(row["req_stb"]),
        },
        "is_repeat": bool(row["is_repeat"]),
        "previous_order_id": row.get("previous_order_id"),
    }


@router.put("/days/{date}", response_model=LoadResult)
async def put_day(date: str, day: DayInput, db: AsyncSession = Depends(get_db)):
    """Загрузка нарядов дня."""
    if day.date != date:
        raise HTTPException(422, "Дата в URL не совпадает с date в теле запроса")
    expected_prefix = f"ORD-{date.replace('-', '')}-"
    if any(not order.order_id.startswith(expected_prefix) for order in day.orders):
        raise HTTPException(422, "Наряды должны иметь order_id с датой из URL")

    day_repo = SqlDayRepo(db)
    orders_repo = SqlOrdersRepo(db)

    await day_repo.upsert(day)
    await orders_repo.upsert_many(date, day.orders)
    return {"status": "loaded", "counts": {"orders": len(day.orders)}}


@router.post("/days/{date}/plan")
async def build_plan(
    date: str,
    request: PlanRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    if not matrix_store.is_loaded():
        raise HTTPException(400, "Матрица не загружена")

    day_repo = SqlDayRepo(db)
    orders_repo = SqlOrdersRepo(db)
    ref_repo = SqlReferenceRepo(db)

    day_row = await day_repo.get(date)
    if not day_row:
        raise HTTPException(404, "День не загружен")

    # Проверка: если события уже приняты — 409
    from api.app.repositories.sql_events_repo import SqlEventsRepo
    has_events = await SqlEventsRepo(db).count_events(date)
    if has_events > 0:
        raise HTTPException(409, f"События уже приняты для {date}")

    staff = await ref_repo.get_staff()
    work_types = await ref_repo.get_work_types()
    service_centers = await ref_repo.get_service_centers()
    if not staff or not work_types or not service_centers:
        raise HTTPException(400, "Справочники не загружены")

    day_input = DayInput(
        date=date,
        now=day_row["model_now"],
        orders=[],
        absent_staff_ids=day_row["absent_staff_ids"] or [],
    )

    orders_dicts = [_flat_to_order(r) for r in await orders_repo.get_by_date(date)]
    apply_duration_forecasts(
        orders_dicts,
        await orders_repo.get_duration_history(),
        work_types,
    )
    matrix = matrix_store.as_matrix()

    start = time.time()
    try:
        pgp_groups = detect_pgp_groups(orders_dicts, work_types, day_input.now)
        pgp_order_ids = {
            order_id for group in pgp_groups for order_id in group.order_ids
        }
        solver_orders = [
            order
            for order in orders_dicts
            if order["order_id"] not in pgp_order_ids
        ]
        if solver_orders:
            plan = await run_in_threadpool(
                solve_vrp,
                date=date,
                day=day_input,
                orders=solver_orders,
                staff=staff,
                work_types=work_types,
                service_centers=service_centers,
                matrix=matrix,
                plan_version=1,
                max_runtime_seconds=request.time_limit_sec if request else 300,
            )
        else:
            plan = Plan(
                date=date,
                plan_version=1,
                as_of=day_input.now,
                routes=[],
                unassigned=[],
                pgp_groups=[],
                cancelled=[],
                alerts=[],
                summary=PlanSummary(),
            )
        plan.pgp_groups = pgp_groups
        plan.alerts = [
            generate_pgp_alert(group, day_input.now) for group in pgp_groups
        ]
        plan.alerts.extend(
            generate_late_risk_alerts(
                plan,
                {order["order_id"]: order for order in orders_dicts},
                day_input.now,
            )
        )
        if plan.summary is None:
            plan.summary = PlanSummary()
        plan.summary.orders_total = len(orders_dicts)
        plan.summary.pgp_orders = len(pgp_order_ids)
        plan.computation_ms = int((time.time() - start) * 1000)
        await SqlPlansRepo(db).save_version(date, plan)
        return plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Ошибка построения плана: {str(e)[:500]}")


def _scenario_metrics(plan: Plan, orders: list[dict]) -> ScenarioMetrics:
    orders_by_id = {order["order_id"]: order for order in orders}
    visits = [
        stop
        for route in plan.routes
        for stop in route.stops
        if stop.type == "VISIT" and stop.order_id
    ]
    in_slot = sum(
        stop.start
        <= datetime.fromisoformat(
            orders_by_id[stop.order_id]["latest_start"]
        )
        for stop in visits
        if stop.order_id in orders_by_id
    )
    risk_ids = {
        alert.order_id
        for alert in plan.alerts
        if alert.type == "LATE_RISK" and alert.order_id
    } | {item.order_id for item in plan.unassigned}
    return ScenarioMetrics(
        orders_total=len(orders),
        visits_planned=len(visits),
        unassigned=len(plan.unassigned),
        in_slot_percent=round(100 * in_slot / len(visits), 1) if visits else 0.0,
        travel_km=round(
            sum(stop.distance_m or 0 for route in plan.routes for stop in route.stops)
            / 1000,
            1,
        ),
        restock_stops=sum(
            stop.type == "RESTOCK"
            for route in plan.routes
            for stop in route.stops
        ),
        risk_orders=len(risk_ids),
    )


@router.post(
    "/days/{date}/scenarios",
    response_model=ScenarioResponse,
)
async def analyze_scenario(
    date: str,
    request: ScenarioRequest,
    db: AsyncSession = Depends(get_db),
) -> ScenarioResponse:
    if not matrix_store.is_loaded():
        raise HTTPException(400, "Матрица не загружена")

    try:
        date_value = date_class.fromisoformat(date)
    except ValueError as exc:
        raise HTTPException(422, "Некорректная дата") from exc
    if date_value.isoformat() != date:
        raise HTTPException(422, "Дата должна быть в формате YYYY-MM-DD")
    day_row = await SqlDayRepo(db).get(date)
    if not day_row:
        raise HTTPException(404, "День не загружен")
    current_plan_data = await SqlPlansRepo(db).get_latest(date)
    if current_plan_data is None:
        raise HTTPException(404, "Сначала постройте план")

    orders_repo = SqlOrdersRepo(db)
    orders = [_flat_to_order(row) for row in await orders_repo.get_by_date(date)]
    reference_repo = SqlReferenceRepo(db)
    staff = await reference_repo.get_staff()
    work_types = await reference_repo.get_work_types()
    service_centers = await reference_repo.get_service_centers()
    if not work_types or not service_centers:
        raise HTTPException(400, "Справочники не загружены")
    baseline = Plan.model_validate(current_plan_data)
    available_staff = [
        person
        for person in staff
        if person.staff_id not in (day_row["absent_staff_ids"] or [])
    ]
    if request.staff_reduction > len(available_staff):
        raise HTTPException(
            422,
            "Количество исключаемых сотрудников превышает доступный состав",
        )
    removed_staff = sorted(
        available_staff,
        key=lambda person: (
            person.experience_years if person.experience_years is not None else -1,
            person.staff_id,
        ),
    )[: request.staff_reduction]
    removed_ids = {person.staff_id for person in removed_staff}
    scenario_staff = []
    for person in staff:
        if person.staff_id in removed_ids or person.staff_id in (
            day_row["absent_staff_ids"] or []
        ):
            continue
        person_data = person.model_dump()
        for field in ("equipment_start", "equipment_capacity"):
            for equipment in ("ONT", "ROUTER", "STB"):
                person_data[field][equipment] += getattr(
                    request.extra_equipment_capacity, equipment
                )
        scenario_staff.append(Staff.model_validate(person_data))

    apply_duration_forecasts(
        orders,
        await orders_repo.get_duration_history(),
        [work_type.model_dump() for work_type in work_types],
    )
    pgp_groups = detect_pgp_groups(
        orders,
        [work_type.model_dump() for work_type in work_types],
        day_row["model_now"],
    )
    pgp_ids = {order_id for group in pgp_groups for order_id in group.order_ids}
    cancelled_ids = {item.order_id for item in baseline.cancelled}
    solver_orders = [
        order
        for order in orders
        if order["order_id"] not in pgp_ids
        and order["order_id"] not in cancelled_ids
    ]
    if solver_orders:
        scenario_plan = await run_in_threadpool(
            solve_vrp,
            date=date,
            day=DayInput(
                date=date,
                now=day_row["model_now"],
                orders=[Order.model_validate(order) for order in solver_orders],
                absent_staff_ids=day_row["absent_staff_ids"] or [],
            ),
            orders=solver_orders,
            staff=scenario_staff,
            work_types=work_types,
            service_centers=service_centers,
            matrix=matrix_store.as_matrix(),
            plan_version=baseline.plan_version + 1,
            max_runtime_seconds=request.time_limit_sec,
        )
    else:
        scenario_plan = Plan(
            date=date,
            plan_version=baseline.plan_version + 1,
            as_of=day_row["model_now"],
            routes=[],
            unassigned=[],
            pgp_groups=[],
            cancelled=[],
            alerts=[],
        )
    scenario_plan.pgp_groups = pgp_groups
    scenario_plan.alerts = generate_late_risk_alerts(
        scenario_plan,
        {order["order_id"]: order for order in orders},
        day_row["model_now"],
    )
    return ScenarioResponse(
        date=date,
        removed_staff_ids=sorted(removed_ids),
        baseline=_scenario_metrics(baseline, orders),
        scenario=_scenario_metrics(scenario_plan, orders),
        unassigned_order_ids=sorted(
            order.order_id for order in scenario_plan.unassigned
        ),
    )


@router.get("/days/{date}/plan", response_model=Plan)
async def get_plan(date: str, db: AsyncSession = Depends(get_db)):
    data = await SqlPlansRepo(db).get_latest(date)
    if not data:
        raise HTTPException(404, "План не построен")
    return data


@router.get("/days/{date}/orders")
async def get_day_orders(date: str, db: AsyncSession = Depends(get_db)):
    rows = await SqlOrdersRepo(db).get_by_date(date)
    if not rows:
        day = await SqlDayRepo(db).get(date)
        if not day:
            raise HTTPException(404, f"День {date} не загружен")

    plan = await SqlPlansRepo(db).get_latest(date)
    assignments: dict[str, dict[str, str | None]] = {}
    if plan:
        for route in plan.get("routes", []):
            for stop in route.get("stops", []):
                if stop.get("type") == "VISIT" and stop.get("order_id"):
                    assignments[stop["order_id"]] = {
                        "status": stop.get("status") or "PLANNED",
                        "assigned_staff_id": route["staff_id"],
                    }
        for item in plan.get("unassigned", []):
            assignments[item["order_id"]] = {
                "status": "UNASSIGNED",
                "assigned_staff_id": None,
            }
        for item in plan.get("cancelled", []):
            assignments[item["order_id"]] = {
                "status": "CANCELLED",
                "assigned_staff_id": None,
            }
        for group in plan.get("pgp_groups", []):
            for order_id in group.get("order_ids", []):
                assignments[order_id] = {"status": "PGP", "assigned_staff_id": None}

    result = []
    for row in rows:
        order = _flat_to_order(row)
        order.update(assignments.get(
            order["order_id"],
            {"status": "UNPLANNED", "assigned_staff_id": None},
        ))
        result.append(order)
    return result