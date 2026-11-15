import unittest
from datetime import datetime

from api.app.services.pgp import detect_pgp_groups


class DetectPgpGroupsTests(unittest.TestCase):
    def test_detects_three_eligible_orders_within_sixty_minutes(self):
        now = datetime.fromisoformat("2026-11-14T12:00:00+05:00")
        orders = [
            {
                "order_id": f"ORD-20261114-{index:04d}",
                "work_type_code": "REPAIR",
                "access_node_id": "AN-0001",
                "registered_at": timestamp,
            }
            for index, timestamp in enumerate(
                (
                    "2026-11-14T09:00:00+05:00",
                    "2026-11-14T09:30:00+05:00",
                    "2026-11-14T10:00:00+05:00",
                    "2026-11-14T10:01:00+05:00",
                ),
                start=1,
            )
        ]

        groups = detect_pgp_groups(
            orders, [{"code": "REPAIR", "pgp_relevant": True}], now
        )

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].access_node_id, "AN-0001")
        self.assertEqual(len(groups[0].order_ids), 3)
        self.assertNotIn("ORD-20261114-0004", groups[0].order_ids)

    def test_ignores_non_pgp_and_not_yet_registered_orders(self):
        now = datetime.fromisoformat("2026-11-14T10:00:00+05:00")
        orders = [
            {
                "order_id": f"ORD-20261114-{index:04d}",
                "work_type_code": "INSTALL",
                "access_node_id": "AN-0001",
                "registered_at": f"2026-11-14T09:{index:02d}:00+05:00",
            }
            for index in range(3)
        ]
        orders.append(
            {
                "order_id": "ORD-20261114-9999",
                "work_type_code": "REPAIR",
                "access_node_id": "AN-0001",
                "registered_at": "2026-11-14T10:01:00+05:00",
            }
        )

        groups = detect_pgp_groups(
            orders,
            [
                {"code": "INSTALL", "pgp_relevant": False},
                {"code": "REPAIR", "pgp_relevant": True},
            ],
            now,
        )

        self.assertEqual(groups, [])


if __name__ == "__main__":
    unittest.main()
