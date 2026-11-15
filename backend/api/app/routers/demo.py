import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import DemoDayResult
from api.app.repositories.db import get_db
from api.app.repositories.sql_day_repo import SqlDayRepo
from api.app.repositories.sql_orders_repo import SqlOrdersRepo
from api.app.services.demo_seed import generate_demo_day

router = APIRouter(tags=["demo"])


@router.post("/demo/days/{date}", response_model=DemoDayResult)
async def prepare_demo_day(date: date, db: AsyncSession = Depends(get_db)):
    if os.getenv("SEED_DEMO_DATA", "").lower() != "true":
        raise HTTPException(404, "Генерация демонстрационных данных отключена")

    date_text = date.isoformat()
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:key)::bigint)"),
        {"key": f"demo-day:{date_text}"},
    )
    day_repo = SqlDayRepo(db)
    orders_repo = SqlOrdersRepo(db)
    existing_day = await day_repo.get(date_text)
    if existing_day:
        orders = await orders_repo.get_by_date(date_text)
        await db.rollback()
        return DemoDayResult(
            status="ready",
            date=date_text,
            generated=False,
            counts={"orders": len(orders)},
        )

    reference_count = await db.scalar(text("SELECT COUNT(*) FROM service_centers"))
    if not reference_count:
        raise HTTPException(409, "Сначала загрузите справочные данные")

    try:
        day, orders = generate_demo_day(date)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await day_repo.upsert(day, commit=False)
    await orders_repo.upsert_many(
        date_text,
        orders,
        replace_existing=True,
        commit=False,
    )
    await db.commit()
    return DemoDayResult(
        status="ready",
        date=date_text,
        generated=True,
        counts={"orders": len(orders)},
    )
