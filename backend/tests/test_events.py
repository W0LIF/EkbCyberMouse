import unittest
from datetime import datetime

from api.app.routers.events import _frozen_stops


class FrozenStopsTests(unittest.TestCase):
    def test_freezes_started_stops_but_not_future_visits(self):
        route = {
            "stops": [
                {"type": "DEPOT_START", "start": "2026-11-14T08:00:00+05:00"},
                {
                    "type": "VISIT",
                    "order_id": "ORD-20261114-0001",
                    "start": "2026-11-14T10:00:00+05:00",
                },
            ]
        }

        frozen = _frozen_stops(
            route, datetime.fromisoformat("2026-11-14T09:00:00+05:00")
        )

        self.assertEqual([stop["type"] for stop in frozen], ["DEPOT_START"])

    def test_freezes_a_visit_after_its_start(self):
        route = {
            "stops": [
                {
                    "type": "VISIT",
                    "order_id": "ORD-20261114-0001",
                    "start": "2026-11-14T09:00:00+05:00",
                }
            ]
        }

        frozen = _frozen_stops(
            route, datetime.fromisoformat("2026-11-14T09:01:00+05:00")
        )

        self.assertEqual(frozen, route["stops"])

    def test_freezes_a_mobile_visit_marked_done_before_its_scheduled_start(self):
        route = {
            "stops": [
                {
                    "type": "VISIT",
                    "order_id": "ORD-20261114-0001",
                    "start": "2026-11-14T10:00:00+05:00",
                    "status": "DONE",
                }
            ]
        }

        frozen = _frozen_stops(
            route, datetime.fromisoformat("2026-11-14T09:00:00+05:00")
        )

        self.assertEqual(frozen, route["stops"])


if __name__ == "__main__":
    unittest.main()
