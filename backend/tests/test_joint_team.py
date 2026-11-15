import unittest
from datetime import datetime, timedelta

from api.app.models import DayInput, TravelMatrix
from solver.app.vrp import solve_vrp


class JointTeamTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.fromisoformat("2026-11-14T08:00:00+05:00")
        self.order = {
            "order_id": "ORD-20261114-0001",
            "work_type_code": "INST_PRIVATE_VLS",
            "technology": "PON",
            "building_id": "B-00001",
            "address": "Private address",
            "lat": 56.81,
            "lon": 60.61,
            "building_type": "PRIVATE",
            "requires_height": True,
            "access_node_id": "AN-0001",
            "registered_at": (self.now - timedelta(days=1)).isoformat(),
            "slot": {
                "start": "2026-11-14T09:00:00+05:00",
                "end": "2026-11-14T12:00:00+05:00",
            },
            "latest_start": "2026-11-14T11:30:00+05:00",
            "deadline": "2026-11-14T17:00:00+05:00",
            "required_equipment": {"ONT": 1, "ROUTER": 1, "STB": 0},
            "is_repeat": False,
        }
        self.staff = [
            {
                "staff_id": f"ST-{index:03d}",
                "service_center_id": "SC-01",
                "profiles": ["INSTALL"],
                "technologies": ["PON"],
                "height_permit": True,
                "shift": {
                    "start": "08:00",
                    "end": "18:00",
                    "break_duration_min": 60,
                    "break_window": {"from": "12:00", "to": "15:00"},
                },
                "equipment_start": {"ONT": 2, "ROUTER": 2, "STB": 1},
                "equipment_capacity": {"ONT": 4, "ROUTER": 4, "STB": 2},
            }
            for index in (1, 2)
        ]
        self.work_types = [
            {
                "code": "INST_PRIVATE_VLS",
                "name": "Private VLS",
                "profiles": ["INSTALL"],
                "duration_min": 120,
                "max_start_delay_min": 10,
                "deadline_kind": "WORKING_DAYS",
                "deadline_value": 5,
                "repeat_deadline_value": None,
                "pgp_relevant": False,
            }
        ]
        self.centers = [
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
        self.matrix = TravelMatrix(
            matrix_id="matrix-1",
            points=["SC-01", "B-00001"],
            durations_sec=[[0, 600], [600, 0]],
            distances_m=[[0, 2000], [2000, 0]],
        )

    def test_private_vls_route_reserves_two_staff_for_one_visit(self):
        plan = solve_vrp(
            date="2026-11-14",
            day=DayInput(
                date="2026-11-14",
                now=self.now,
                orders=[],
                absent_staff_ids=[],
            ),
            orders=[self.order],
            staff=self.staff,
            work_types=self.work_types,
            service_centers=self.centers,
            matrix=self.matrix,
            max_runtime_seconds=3,
        )

        self.assertEqual(len(plan.routes), 1)
        self.assertEqual(plan.routes[0].team_staff_ids, ["ST-001", "ST-002"])
        self.assertEqual(
            sum(stop.type == "VISIT" for stop in plan.routes[0].stops),
            1,
        )
        self.assertEqual(plan.unassigned, [])

    def test_private_vls_is_unassigned_without_two_qualified_staff(self):
        plan = solve_vrp(
            date="2026-11-14",
            day=DayInput(
                date="2026-11-14",
                now=self.now,
                orders=[],
                absent_staff_ids=[],
            ),
            orders=[self.order],
            staff=self.staff[:1],
            work_types=self.work_types,
            service_centers=self.centers,
            matrix=self.matrix,
            max_runtime_seconds=3,
        )

        self.assertEqual(plan.routes, [])
        self.assertEqual(len(plan.unassigned), 1)
        self.assertEqual(plan.unassigned[0].reason_code, "NO_QUALIFIED_STAFF")


if __name__ == "__main__":
    unittest.main()
