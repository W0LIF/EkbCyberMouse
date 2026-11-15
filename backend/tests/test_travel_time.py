import unittest
from datetime import datetime

from api.app.models import HourlyFactor, TravelMatrix
from api.app.services.matrix_store import MatrixStore
from api.app.services.travel_time import adjusted_travel_seconds


class HourlyTravelTimeTests(unittest.TestCase):
    def setUp(self):
        self.factors = [HourlyFactor(hour=9, factor=1.5)]

    def test_uses_departure_hour_in_business_timezone(self):
        before_traffic = datetime.fromisoformat("2026-11-14T03:59:00+00:00")
        during_traffic = datetime.fromisoformat("2026-11-14T04:00:00+00:00")

        self.assertEqual(
            adjusted_travel_seconds(601, before_traffic, self.factors),
            601,
        )
        self.assertEqual(
            adjusted_travel_seconds(601, during_traffic, self.factors),
            902,
        )

    def test_matrix_store_applies_factor_only_when_departure_is_given(self):
        store = MatrixStore()
        store.store(
            TravelMatrix(
                matrix_id="matrix-1",
                points=["SC-01", "B-00001"],
                durations_sec=[[0, 601], [601, 0]],
                distances_m=[[0, 1000], [1000, 0]],
                hourly_factors=self.factors,
            )
        )

        base_duration, _ = store.get("SC-01", "B-00001")
        adjusted_duration, distance = store.get(
            "SC-01",
            "B-00001",
            datetime.fromisoformat("2026-11-14T09:00:00+05:00"),
        )

        self.assertEqual(base_duration, 601)
        self.assertEqual(adjusted_duration, 902)
        self.assertEqual(distance, 1000)


if __name__ == "__main__":
    unittest.main()
