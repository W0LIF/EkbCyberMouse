import unittest
from datetime import date, datetime, timedelta

from api.app.services.demo_seed import (
    DEMO_DATE,
    DEMO_MAX_DATE,
    DEMO_MIN_DATE,
    _read_json,
    generate_demo_day,
)


class GenerateDemoDayTests(unittest.TestCase):
    def test_generates_dates_more_than_a_year_away(self):
        for target in (date(2024, 11, 13), date(2028, 11, 15)):
            with self.subTest(target=target):
                day, orders = generate_demo_day(target)

                self.assertEqual(day.date, target.isoformat())
                self.assertEqual(day.now.date(), target)
                self.assertEqual(len(orders), 30)
                self.assertTrue(
                    all(order.order_id.startswith(f"ORD-{target:%Y%m%d}-") for order in orders)
                )
                self.assertTrue(
                    all(order.slot.start.date() == target for order in orders)
                )

    def test_shifts_all_order_timestamps_by_the_same_number_of_days(self):
        target = date(2028, 11, 15)
        _, orders = generate_demo_day(target)
        raw_template = next(
            item
            for item in _read_json("orders_train.json")
            if item["order_id"] == f"ORD-{DEMO_DATE.replace('-', '')}-0001"
        )
        template = datetime.fromisoformat(raw_template["slot"]["start"])
        order = next(item for item in orders if item.order_id.endswith("-0001"))

        self.assertEqual(
            order.slot.start,
            template + (target - date.fromisoformat(DEMO_DATE)),
        )

    def test_rejects_dates_outside_supported_range(self):
        for target in (
            DEMO_MIN_DATE - timedelta(days=1),
            DEMO_MAX_DATE + timedelta(days=1),
        ):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    generate_demo_day(target)


if __name__ == "__main__":
    unittest.main()
