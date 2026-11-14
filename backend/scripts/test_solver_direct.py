"""Тест солвера напрямую, без HTTP — видим полный traceback."""
import sys, traceback
from datetime import datetime, timedelta, timezone

# Добавляем корень backend в sys.path
sys.path.insert(0, r"C:\Githab\EkbCyberMouse\backend")

from solver.app.vrp import solve_vrp
from api.app.models import DayInput, TravelMatrix

now = datetime(2026, 10, 26, 8, 30, tzinfo=timezone(timedelta(hours=5)))

day = {
    "date": "2026-10-26",
    "now": now.isoformat(),
    "orders": [],
    "absent_staff_ids": [],
}

orders = [
    {
        "order_id": "ORD-20261026-0001",
        "work_type_code": "REPAIR",
        "technology": "PON",
        "building_id": "B-00001",
        "address": "ул. Тестовая 1",
        "lat": 56.81,
        "lon": 60.61,
        "building_type": "MKD",
        "requires_height": False,
        "access_node_id": "AN-0001",
        "registered_at": (now - timedelta(days=1)).isoformat(),
        "slot": {
            "start": (now + timedelta(hours=1.5)).isoformat(),
            "end": (now + timedelta(hours=3.5)).isoformat(),
        },
        "latest_start": (now + timedelta(hours=3.5)).isoformat(),
        "deadline": (now + timedelta(hours=25)).isoformat(),
        "required_equipment": {"ONT": 0, "ROUTER": 0, "STB": 0},
        "is_repeat": False,
    },
    {
        "order_id": "ORD-20261026-0002",
        "work_type_code": "REPAIR",
        "technology": "PON",
        "building_id": "B-00002",
        "address": "ул. Тестовая 2",
        "lat": 56.82,
        "lon": 60.62,
        "building_type": "MKD",
        "requires_height": False,
        "access_node_id": "AN-0002",
        "registered_at": (now - timedelta(days=1)).isoformat(),
        "slot": {
            "start": (now + timedelta(hours=5)).isoformat(),
            "end": (now + timedelta(hours=7)).isoformat(),
        },
        "latest_start": (now + timedelta(hours=7)).isoformat(),
        "deadline": (now + timedelta(hours=25)).isoformat(),
        "required_equipment": {"ONT": 0, "ROUTER": 0, "STB": 0},
        "is_repeat": False,
    },
]

staff = [
    {
        "staff_id": "ST-001",
        "display_name": "Сотрудник 1",
        "service_center_id": "SC-01",
        "profiles": ["LTP3", "INSTALL"],
        "technologies": ["PON", "FTTB"],
        "height_permit": True,
        "shift": {"start": "09:00", "end": "18:00", "break_duration_min": 60, "break_window": {"from": "12:00", "to": "15:00"}},
        "equipment_start": {"ONT": 5, "ROUTER": 5, "STB": 2},
        "equipment_capacity": {"ONT": 10, "ROUTER": 10, "STB": 5},
    },
    {
        "staff_id": "ST-002",
        "display_name": "Сотрудник 2",
        "service_center_id": "SC-01",
        "profiles": ["LTP3", "INSTALL"],
        "technologies": ["PON", "FTTB"],
        "height_permit": True,
        "shift": {"start": "09:00", "end": "18:00", "break_duration_min": 60, "break_window": {"from": "12:00", "to": "15:00"}},
        "equipment_start": {"ONT": 5, "ROUTER": 5, "STB": 2},
        "equipment_capacity": {"ONT": 10, "ROUTER": 10, "STB": 5},
    },
]

work_types = [
    {"code": "REPAIR", "name": "Ремонт", "profiles": ["LTP3"], "duration_min": 60,
     "max_start_delay_min": None, "deadline_kind": "HOURS", "deadline_value": 24,
     "repeat_deadline_value": 12, "pgp_relevant": True},
    {"code": "INST_PON_MKD", "name": "Инсталляция", "profiles": ["INSTALL"],
     "duration_min": 90, "max_start_delay_min": 10, "deadline_kind": "WORKING_DAYS",
     "deadline_value": 3, "repeat_deadline_value": None, "pgp_relevant": False},
]

service_centers = [
    {
        "service_center_id": "SC-01",
        "name": "СЦ-1",
        "address": "ул. Ленина, 1",
        "lat": 56.8,
        "lon": 60.6,
        "opening_hours": {"open": "08:00", "close": "21:00"},
        "restock_duration_min": 15,
    },
]

matrix = {
    "matrix_id": "test-v1",
    "points": ["SC-01", "B-00001", "B-00002"],
    "durations_sec": [[0, 600, 900], [600, 0, 300], [900, 300, 0]],
    "distances_m": [[0, 2000, 3000], [2000, 0, 1000], [3000, 1000, 0]],
}

try:
    plan = solve_vrp(
        date="2026-10-26",
        day=DayInput(date="2026-10-26", now=now, orders=[], absent_staff_ids=[]),
        orders=orders,
        staff=staff,
        work_types=work_types,
        service_centers=service_centers,
        matrix=TravelMatrix(**matrix),
    )
    print("✅ План построен!")
    print(f"  Маршрутов: {len(plan.routes)}")
    print(f"  Unassigned: {len(plan.unassigned)}")
    if plan.summary:
        print(f"  Summary: {plan.summary}")
except Exception:
    print("\n" + "=" * 60)
    print("ОШИБКА СОЛВЕРА:")
    print("=" * 60)
    traceback.print_exc()
    print("=" * 60)
