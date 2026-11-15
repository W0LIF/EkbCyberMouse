from datetime import date, datetime
from math import ceil

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import (
    MobileActionRequest,
    MobileRoute,
    MobileVisit,
    Plan,
)
from api.app.repositories.db import get_db
from api.app.repositories.sql_mobile_repo import SqlMobileRepo
from api.app.repositories.sql_orders_repo import SqlOrdersRepo
from api.app.repositories.sql_plans_repo import SqlPlansRepo
from api.app.repositories.sql_reference_repo import SqlReferenceRepo

router = APIRouter(tags=["employee-mobile"])


async def _mobile_route(
    date_value: date,
    staff_id: str,
    db: AsyncSession,
) -> MobileRoute:
    date_text = date_value.isoformat()
    plan_data = await SqlPlansRepo(db).get_latest(date_text)
    if plan_data is None:
        raise HTTPException(404, "План на дату не построен")

    route = next(
        (item for item in plan_data["routes"] if item["staff_id"] == staff_id),
        None,
    )
    if route is None:
        raise HTTPException(404, "Маршрут сотрудника не найден")

    staff = await SqlReferenceRepo(db).get_staff_by_id(staff_id)
    order_rows = {
        row["order_id"]: row
        for row in await SqlOrdersRepo(db).get_by_date(date_text)
    }
    actions = await SqlMobileRepo(db).get_actions(date_value, staff_id)
    visits = []
    for stop in route["stops"]:
        order_id = stop.get("order_id")
        if stop["type"] != "VISIT" or not order_id:
            continue
        order = order_rows.get(order_id)
        if order is None:
            raise HTTPException(
                500,
                f"В плане есть наряд {order_id}, отсутствующий в базе",
            )
        timestamps = actions.get(order_id, {})
        visits.append(
            MobileVisit(
                order_id=order_id,
                address=order["address"],
                lat=order["lat"],
                lon=order["lon"],
                work_type_code=order["work_type_code"],
                technology=order["technology"],
                scheduled_start=stop["start"],
                scheduled_end=stop["end"],
                status=stop.get("status") or "PLANNED",
                call_at=timestamps.get("CALL_CUSTOMER"),
                arrived_at=timestamps.get("ARRIVED"),
                completed_at=timestamps.get("COMPLETED"),
            )
        )
    return MobileRoute(
        date=date_text,
        staff_id=staff_id,
        team_staff_ids=route.get("team_staff_ids"),
        staff_name=staff.display_name if staff else None,
        visits=visits,
    )


@router.get(
    "/mobile/days/{date}/routes/{staff_id}",
    response_model=MobileRoute,
)
async def get_mobile_route(
    date: date,
    staff_id: str,
    db: AsyncSession = Depends(get_db),
) -> MobileRoute:
    return await _mobile_route(date, staff_id, db)


@router.post(
    "/mobile/days/{date}/routes/{staff_id}/visits/{order_id}/actions",
    response_model=MobileRoute,
)
async def record_mobile_action(
    date: date,
    staff_id: str,
    order_id: str,
    request: MobileActionRequest,
    db: AsyncSession = Depends(get_db),
) -> MobileRoute:
    date_text = date.isoformat()
    plans_repo = SqlPlansRepo(db)
    plan_data = await plans_repo.get_latest(date_text)
    if plan_data is None:
        raise HTTPException(404, "План на дату не построен")
    route = next(
        (item for item in plan_data["routes"] if item["staff_id"] == staff_id),
        None,
    )
    if route is None:
        raise HTTPException(404, "Маршрут сотрудника не найден")
    stop = next(
        (
            item
            for item in route["stops"]
            if item.get("order_id") == order_id and item["type"] == "VISIT"
        ),
        None,
    )
    if stop is None:
        raise HTTPException(404, "Наряд не найден в маршруте сотрудника")

    mobile_repo = SqlMobileRepo(db)
    actions = await mobile_repo.get_actions(date, staff_id)
    timestamps = actions.get(order_id, {})
    if request.action in timestamps:
        await db.rollback()
        return await _mobile_route(date, staff_id, db)
    if "COMPLETED" in timestamps:
        raise HTTPException(409, "Наряд уже завершен")
    if request.action == "COMPLETED" and "ARRIVED" not in timestamps:
        raise HTTPException(409, "Сначала необходимо отметить прибытие")
    if (
        request.action == "COMPLETED"
        and timestamps["ARRIVED"] > request.occurred_at
    ):
        raise HTTPException(422, "Завершение не может быть раньше прибытия")
    inserted = await mobile_repo.record_action(
        date,
        staff_id,
        order_id,
        request.action,
        request.occurred_at,
    )
    if inserted:
        if request.action == "ARRIVED":
            stop["status"] = "IN_PROGRESS"
        elif request.action == "COMPLETED":
            stop["status"] = "DONE"
            order = await SqlOrdersRepo(db).get_by_id(date_text, order_id)
            if order is None:
                raise HTTPException(500, "Наряд маршрута отсутствует в базе")
            duration_min = max(
                1,
                ceil(
                    (
                        request.occurred_at - timestamps["ARRIVED"]
                    ).total_seconds()
                    / 60
                ),
            )
            await db.execute(
                text("""
                    INSERT INTO order_facts (
                        order_id, work_type_code, technology,
                        actual_duration_min, occurred_at
                    )
                    VALUES (:order_id, :work_type, :technology, :duration, :occurred_at)
                    ON CONFLICT (order_id) DO UPDATE SET
                        work_type_code = EXCLUDED.work_type_code,
                        technology = EXCLUDED.technology,
                        actual_duration_min = EXCLUDED.actual_duration_min,
                        occurred_at = EXCLUDED.occurred_at
                """),
                {
                    "order_id": order_id,
                    "work_type": order["work_type_code"],
                    "technology": order["technology"],
                    "duration": duration_min,
                    "occurred_at": request.occurred_at,
                },
            )
        plan = Plan.model_validate(plan_data)
        plan.plan_version += 1
        plan.as_of = max(plan.as_of, request.occurred_at)
        await plans_repo.save_version(date_text, plan, commit=False)
        await db.commit()
    else:
        await db.rollback()

    return await _mobile_route(date, staff_id, db)
