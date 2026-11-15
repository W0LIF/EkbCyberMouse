import json
import logging
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import text

from api.app.models import DayInput, Order, ReferenceData, TravelMatrix
from api.app.repositories.db import AsyncSessionLocal
from api.app.repositories.sql_day_repo import SqlDayRepo
from api.app.repositories.sql_orders_repo import SqlOrdersRepo
from api.app.repositories.sql_reference_repo import SqlReferenceRepo
from api.app.services.matrix_store import matrix_store

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DEMO_DATE = "2026-11-14"
DEMO_NOW = datetime.fromisoformat("2026-11-14T08:30:00+05:00")
DEMO_MIN_DATE = date(1900, 1, 1)
DEMO_MAX_DATE = date(2100, 12, 31)


def _read_json(name: str):
    with (DATA_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


async def seed_demo_data_if_empty() -> None:
    matrix = TravelMatrix.model_validate(_read_json("travel_matrix.json"))
    matrix_store.store(matrix)

    async with AsyncSessionLocal() as session:
        count = await session.scalar(text("SELECT COUNT(*) FROM service_centers"))
        if count:
            return

        reference = ReferenceData.model_validate({
            "service_centers": _read_json("service_centers.json"),
            "staff": _read_json("staff.json"),
            "access_nodes": _read_json("access_nodes.json"),
            "work_types": _read_json("work_types.json"),
        })
        orders = [
            Order.model_validate(item)
            for item in _read_json("orders_train.json")
            if item["order_id"].startswith(f"ORD-{DEMO_DATE.replace('-', '')}-")
        ]
        day = DayInput(
            date=DEMO_DATE,
            now=DEMO_NOW,
            orders=orders,
            absent_staff_ids=[],
        )

        await SqlReferenceRepo(session).replace_all(reference)
        await SqlDayRepo(session).upsert(day)
        await SqlOrdersRepo(session).upsert_many(DEMO_DATE, orders)
        logger.info("Loaded demo dataset: %d staff, %d orders", len(reference.staff), len(orders))


def generate_demo_day(target_date: date) -> tuple[DayInput, list[Order]]:
    """Shift the bundled synthetic day to another calendar date."""
    if not DEMO_MIN_DATE <= target_date <= DEMO_MAX_DATE:
        raise ValueError(
            f"Демо-даты должны быть в диапазоне "
            f"{DEMO_MIN_DATE.isoformat()}—{DEMO_MAX_DATE.isoformat()}"
        )

    template_date = date.fromisoformat(DEMO_DATE)
    day_shift = target_date - template_date
    prefix = f"ORD-{target_date:%Y%m%d}-"
    templates = [
        order
        for order in _read_json("orders_train.json")
        if order["order_id"].startswith(f"ORD-{DEMO_DATE.replace('-', '')}-")
    ]
    if not templates:
        raise RuntimeError("В orders_train.json отсутствуют демо-наряды")

    order_id_map = {
        template["order_id"]: f"{prefix}{index:04d}"
        for index, template in enumerate(templates, start=1)
    }

    def shift_timestamp(value: str) -> str:
        return (datetime.fromisoformat(value) + day_shift).isoformat(timespec="seconds")

    orders = []
    for template in templates:
        data = deepcopy(template)
        data["order_id"] = order_id_map[template["order_id"]]
        data["registered_at"] = shift_timestamp(data["registered_at"])
        data["slot"]["start"] = shift_timestamp(data["slot"]["start"])
        data["slot"]["end"] = shift_timestamp(data["slot"]["end"])
        data["latest_start"] = shift_timestamp(data["latest_start"])
        data["deadline"] = shift_timestamp(data["deadline"])
        if data.get("previous_order_id") in order_id_map:
            data["previous_order_id"] = order_id_map[data["previous_order_id"]]
        orders.append(Order.model_validate(data))

    now = DEMO_NOW + day_shift
    return (
        DayInput(
            date=target_date.isoformat(),
            now=now,
            orders=orders,
            absent_staff_ids=[],
        ),
        orders,
    )
