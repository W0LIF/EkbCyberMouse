import unittest
from datetime import datetime
from types import SimpleNamespace

from api.app.models import PgpGroup
from api.app.services.alerts import (
    generate_late_risk_alerts,
    generate_new_pgp_alerts,
)


class GenerateNewPgpAlertsTests(unittest.TestCase):
    def test_creates_alert_when_existing_group_gains_an_order(self):
        now = datetime.fromisoformat("2026-11-14T08:00:00+05:00")
        previous = [
            {"group_id": "PGP-AN-0001-01", "order_ids": ["ORD-1", "ORD-2", "ORD-3"]}
        ]
        expanded = PgpGroup(
            group_id="PGP-AN-0001-01",
            access_node_id="AN-0001",
            order_ids=["ORD-1", "ORD-2", "ORD-3", "ORD-4"],
            detected_at=now,
            action="TRANSFER_TO_STATION",
        )

        alerts = generate_new_pgp_alerts([expanded], previous, now)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].type, "PGP_DETECTED")
        self.assertEqual(alerts[0].group_id, expanded.group_id)

    def test_does_not_repeat_alert_for_unchanged_group_composition(self):
        now = datetime.fromisoformat("2026-11-14T08:00:00+05:00")
        group = PgpGroup(
            group_id="PGP-AN-0001-01",
            access_node_id="AN-0001",
            order_ids=["ORD-1", "ORD-2", "ORD-3"],
            detected_at=now,
            action="TRANSFER_TO_STATION",
        )

        alerts = generate_new_pgp_alerts(
            [group],
            [{"group_id": group.group_id, "order_ids": group.order_ids}],
            now,
        )

        self.assertEqual(alerts, [])


class GenerateLateRiskAlertsTests(unittest.TestCase):
    def test_creates_alert_when_forecast_start_exceeds_latest_start(self):
        forecast_start = datetime.fromisoformat("2026-11-14T10:15:00+05:00")
        latest_start = datetime.fromisoformat("2026-11-14T10:00:00+05:00")
        now = datetime.fromisoformat("2026-11-14T08:00:00+05:00")
        plan = SimpleNamespace(
            routes=[
                SimpleNamespace(
                    staff_id="ST-001",
                    stops=[
                        SimpleNamespace(
                            type="VISIT",
                            order_id="ORD-20261114-0001",
                            start=forecast_start,
                        )
                    ],
                )
            ]
        )

        alerts = generate_late_risk_alerts(
            plan,
            {
                "ORD-20261114-0001": {
                    "latest_start": latest_start.isoformat(),
                }
            },
            now,
        )

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].type, "LATE_RISK")
        self.assertEqual(alerts[0].order_id, "ORD-20261114-0001")
        self.assertEqual(alerts[0].staff_id, "ST-001")
        self.assertEqual(alerts[0].forecast_start, forecast_start)
        self.assertEqual(alerts[0].lateness_min, 15)
        self.assertEqual(alerts[0].created_at, now)

    def test_does_not_create_alert_for_a_visit_that_has_already_started(self):
        started = datetime.fromisoformat("2026-11-14T07:45:00+05:00")
        now = datetime.fromisoformat("2026-11-14T08:00:00+05:00")
        plan = SimpleNamespace(
            routes=[
                SimpleNamespace(
                    staff_id="ST-001",
                    stops=[
                        SimpleNamespace(
                            type="VISIT",
                            order_id="ORD-20261114-0001",
                            start=started,
                        )
                    ],
                )
            ]
        )

        alerts = generate_late_risk_alerts(
            plan,
            {
                "ORD-20261114-0001": {
                    "latest_start": "2026-11-14T07:30:00+05:00",
                }
            },
            now,
        )

        self.assertEqual(alerts, [])


if __name__ == "__main__":
    unittest.main()
