from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from api.app.models import Plan, DayInput, LoadResult, Order, TimeWindow, Equipment
from api.app.services.matrix_store import matrix_store
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
    day_repo = SqlDayRepo(db)
    orders_repo = SqlOrdersRepo(db)

    await day_repo.upsert(day)
    await orders_repo.upsert_many(date, day.orders)
    return {"status": "loaded", "counts": {"orders": len(day.orders)}}


@router.post("/days/{date}/plan")
async def build_plan(date: str, db: AsyncSession = Depends(get_db)):
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
    matrix = matrix_store.as_matrix()

    # Debug: log first order's equipment
    if orders_dicts:
        with open("plan_debug.log", "a") as dbg:
            dbg.write(f"First order: {orders_dicts[0]['order_id']} eq={orders_dicts[0].get('required_equipment')}\n")
            dbg.write(f"Orders count: {len(orders_dicts)}, Staff: {len(staff)}\n")

    start = time.time()
    try:
        plan = solve_vrp(
            date=date,
            day=day_input,
            orders=orders_dicts,
            staff=staff,
            work_types=work_types,
            service_centers=service_centers,
            matrix=matrix,
            plan_version=1,
            max_runtime_seconds=120,
        )
        plan.computation_ms = int((time.time() - start) * 1000)
        await SqlPlansRepo(db).save_version(date, plan)
        return plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Ошибка построения плана: {str(e)[:500]}")


@router.get("/days/{date}/plan", response_model=Plan)
async def get_plan(date: str, db: AsyncSession = Depends(get_db)):
    data = await SqlPlansRepo(db).get_latest(date)
    if not data:
        raise HTTPException(404, "План не построен")
    return data