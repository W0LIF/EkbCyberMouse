"""Тест солвера напрямую, без HTTP — видим полный traceback."""
import sys, traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Добавляем корень backend в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from solver.app.vrp import solve_vrp
from api.app.models import DayInput, TravelMatrix

now = datetime(2026, 10, 26, 11, 5, tzinfo=timezone(timedelta(hours=5)))

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
    assert len(plan.routes) == 1
    route = plan.routes[0]
    assert route.stops[0].type == "DEPOT_START"
    assert route.stops[0].start >= now
    assert route.stops[-1].type == "DEPOT_END"
    assert sum(stop.type == "VISIT" for stop in route.stops) == 2
    assert sum(stop.type == "BREAK" for stop in route.stops) == 1
    assert route.stops[-1].arrival <= datetime(2026, 10, 26, 18, 0, tzinfo=now.tzinfo)
    orders_by_id = {order["order_id"]: order for order in orders}
    for previous, current in zip(route.stops, route.stops[1:]):
        assert current.start >= previous.end
        if current.type == "BREAK":
            assert current.location_id == previous.location_id
            assert current.travel_sec == 0
            assert datetime(2026, 10, 26, 12, 0, tzinfo=now.tzinfo) <= current.start
            assert current.start <= datetime(2026, 10, 26, 15, 0, tzinfo=now.tzinfo)
            assert current.end - current.start >= timedelta(minutes=60)
        elif current.type in ("VISIT", "DEPOT_END"):
            from_idx = matrix["points"].index(previous.location_id)
            to_idx = matrix["points"].index(current.location_id)
            assert current.travel_sec is not None
            travel_sec = current.travel_sec
            assert travel_sec == matrix["durations_sec"][from_idx][to_idx]
            assert current.arrival >= previous.end + timedelta(
                seconds=travel_sec
            )
            if current.type == "VISIT":
                assert current.order_id is not None
                order = orders_by_id[current.order_id]
                assert current.start >= datetime.fromisoformat(order["slot"]["start"])
                assert current.start <= datetime.fromisoformat(order["latest_start"])
                assert current.end - current.start == timedelta(minutes=60)
    assert route.totals is not None
    assert route.totals.travel_sec == sum(
        stop.travel_sec or 0 for stop in route.stops
    )

    restock_order = {
        **orders[0],
        "required_equipment": {"ONT": 6, "ROUTER": 0, "STB": 0},
    }
    restock_plan = solve_vrp(
        date="2026-10-26",
        day=DayInput(date="2026-10-26", now=now, orders=[], absent_staff_ids=[]),
        orders=[restock_order],
        staff=[staff[0]],
        work_types=work_types,
        service_centers=service_centers,
        matrix=TravelMatrix(**matrix),
        max_runtime_seconds=3,
    )
    assert not restock_plan.unassigned
    restock_route = restock_plan.routes[0]
    restock_stop = next(stop for stop in restock_route.stops if stop.type == "RESTOCK")
    restock_visit = next(stop for stop in restock_route.stops if stop.type == "VISIT")
    assert restock_stop.location_id == "SC-01"
    assert restock_stop.end - restock_stop.start >= timedelta(minutes=15)
    assert restock_stop.equipment_after is not None
    assert restock_stop.equipment_after.ONT == 10
    assert restock_visit.equipment_after is not None
    assert restock_visit.equipment_after.ONT == 4
    assert restock_route.stops.index(restock_stop) < restock_route.stops.index(restock_visit)
    for previous, current in zip(restock_route.stops, restock_route.stops[1:]):
        assert current.start >= previous.end
        if current.type in ("RESTOCK", "VISIT", "DEPOT_END"):
            from_idx = matrix["points"].index(previous.location_id)
            to_idx = matrix["points"].index(current.location_id)
            travel_sec = matrix["durations_sec"][from_idx][to_idx]
            assert current.travel_sec == travel_sec
            assert current.arrival >= previous.end + timedelta(seconds=travel_sec)
        if current.equipment_after is not None:
            assert min(
                current.equipment_after.ONT,
                current.equipment_after.ROUTER,
                current.equipment_after.STB,
            ) >= 0

    over_capacity_order = {
        **restock_order,
        "required_equipment": {"ONT": 11, "ROUTER": 0, "STB": 0},
    }
    capacity_plan = solve_vrp(
        date="2026-10-26",
        day=DayInput(date="2026-10-26", now=now, orders=[], absent_staff_ids=[]),
        orders=[over_capacity_order],
        staff=[staff[0]],
        work_types=work_types,
        service_centers=service_centers,
        matrix=TravelMatrix(**matrix),
        max_runtime_seconds=3,
    )
    assert not any(
        stop.type == "VISIT"
        for capacity_route in capacity_plan.routes
        for stop in capacity_route.stops
    )
    assert [item.order_id for item in capacity_plan.unassigned] == [
        over_capacity_order["order_id"]
    ]
    print("Solver smoke test passed")
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
    raise
