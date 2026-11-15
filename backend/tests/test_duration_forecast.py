import unittest

from api.app.services.duration_forecast import apply_duration_forecasts


class DurationForecastTests(unittest.TestCase):
    def test_uses_median_for_sufficient_matching_history(self):
        orders = [
            {
                "work_type_code": "REPAIR",
                "technology": "PON",
            }
        ]
        history = [
            {
                "work_type_code": "REPAIR",
                "technology": "PON",
                "actual_duration_min": duration,
            }
            for duration in (20, 35, 90)
        ]

        apply_duration_forecasts(
            orders,
            history,
            [{"code": "REPAIR", "duration_min": 60}],
        )

        self.assertEqual(orders[0]["duration_estimate_min"], 35)
        self.assertEqual(orders[0]["duration_source"], "HISTORY")

    def test_falls_back_to_norm_when_history_is_insufficient(self):
        orders = [
            {
                "work_type_code": "REPAIR",
                "technology": "PON",
            }
        ]
        history = [
            {
                "work_type_code": "REPAIR",
                "technology": "PON",
                "actual_duration_min": 35,
            }
        ]

        apply_duration_forecasts(
            orders,
            history,
            [{"code": "REPAIR", "duration_min": 60}],
        )

        self.assertEqual(orders[0]["duration_estimate_min"], 60)
        self.assertEqual(orders[0]["duration_source"], "NORM")


if __name__ == "__main__":
    unittest.main()
