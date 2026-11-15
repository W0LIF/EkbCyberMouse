import unittest
from datetime import datetime

from api.app.models import DayInput, TravelMatrix
from solver.app.vrp import solve_vrp


class SolverEligibilityTests(unittest.TestCase):
    def test_routes_orders_only_to_staff_with_matching_technology(self):
        now = datetime.fromisoformat("2026-11-14T08:00:00+05:00")
        staff = [
            {
                "staff_id": "ST-001",
                "service_center_id": "SC-01",
                "profiles": ["INSTALL"],
                "technologies": ["PON"],
                "height_permit": False,
                "shift": {
                    "start": "08:00",
                    "end": "18:00",
                    "break_duration_min": 60,
                    "break_window": {"from": "12:00", "to": "15:00"},
                },
                "equipment_start": {"ONT": 2, "ROUTER": 2, "STB": 1},
                "equipment_capacity": {"ONT": 4, "ROUTER": 4, "STB": 2},
            },
            {
                "staff_id": "ST-002",
                "service_center_id": "SC-01",
                "profiles": ["INSTALL"],
                "technologies": ["FTTB"],
                "height_permit": False,
                "shift": {
                    "start": "08:00",
                    "end": "18:00",
                    "break_duration_min": 60,
                    "break_window": {"from": "12:00", "to": "15:00"},
                },
                "equipment_start": {"ONT": 2, "ROUTER": 2, "STB": 1},
                "equipment_capacity": {"ONT": 4, "ROUTER": 4, "STB": 2},
            },
        ]
        work_types = [
            {
                "code": code,
                "name": code,
                "profiles": ["INSTALL"],
                "duration_min": 60,
                "max_start_delay_min": 10,
                "deadline_kind": "WORKING_DAYS",
                "deadline_value": 3,
                "repeat_deadline_value": None,
                "pgp_relevant": False,
            }
            for code in ("INST_PON_MKD", "INST_FTTB_MKD")
        ]
        orders = []
        for index, (code, technology) in enumerate(
            (("INST_PON_MKD", "PON"), ("INST_FTTB_MKD", "FTTB")),
            start=1,
        ):
            orders.append(
                {
                    "order_id": f"ORD-20261114-{index:04d}",
                    "work_type_code": code,
                    "technology": technology,
                    "building_id": f"B-{index:05d}",
                    "address": f"Address {index}",
                    "lat": 56.81,
                    "lon": 60.61,
                    "building_type": "MKD",
                    "requires_height": False,
                    "access_node_id": f"AN-{index:04d}",
                    "registered_at": "2026-11-13T10:00:00+05:00",
                    "slot": {
                        "start": "2026-11-14T09:00:00+05:00",
                        "end": "2026-11-14T11:00:00+05:00",
                    },
                    "latest_start": "2026-11-14T10:30:00+05:00",
                    "deadline": "2026-11-14T15:00:00+05:00",
                    "required_equipment": {"ONT": 1, "ROUTER": 1, "STB": 0},
                    "is_repeat": False,
                }
            )
        service_centers = [
            {
                "service_center_id": "SC-01",
                "name": "SC",
                "address": "SC address",
                "lat": 56.8,
                "lon": 60.6,
                "opening_hours": {"open": "08:00", "close": "21:00"},
                "restock_duration_min": 15,
            }
        ]
        matrix = TravelMatrix(
            matrix_id="matrix-1",
            points=["SC-01", "B-00001", "B-00002"],
            durations_sec=[
                [0, 600, 600],
                [600, 0, 300],
                [600, 300, 0],
            ],
            distances_m=[
                [0, 1000, 1000],
                [1000, 0, 500],
                [1000, 500, 0],
            ],
        )

        plan = solve_vrp(
            date="2026-11-14",
            day=DayInput(
                date="2026-11-14",
                now=now,
                orders=[],
                absent_staff_ids=[],
            ),
            orders=orders,
            staff=staff,
            work_types=work_types,
            service_centers=service_centers,
            matrix=matrix,
            max_runtime_seconds=4,
        )

        assignments = {
            stop.order_id: route.staff_id
            for route in plan.routes
            for stop in route.stops
            if stop.type == "VISIT"
        }
        self.assertEqual(assignments, {
            "ORD-20261114-0001": "ST-001",
            "ORD-20261114-0002": "ST-002",
        })
        self.assertEqual(plan.unassigned, [])


if __name__ == "__main__":
    unittest.main()
