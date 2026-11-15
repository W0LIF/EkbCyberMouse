from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from api.app.models import PgpGroup


def detect_pgp_groups(
    orders: list[dict], work_types: list, now: datetime
) -> list[PgpGroup]:
    pgp_codes = {
        item.code if hasattr(item, "code") else item["code"]
        for item in work_types
        if (
            item.pgp_relevant
            if hasattr(item, "pgp_relevant")
            else item.get("pgp_relevant")
        )
    }
    node_orders: dict[str, list[dict]] = defaultdict(list)
    for order in orders:
        if order["work_type_code"] in pgp_codes and order.get("access_node_id"):
            registered_at = datetime.fromisoformat(order["registered_at"])
            if registered_at <= now:
                node_orders[order["access_node_id"]].append(order)

    groups = []
    for node_id, node_items in node_orders.items():
        sorted_items = sorted(
            node_items, key=lambda item: item["registered_at"]
        )
        start = 0
        group_index = 1
        while start < len(sorted_items):
            first = datetime.fromisoformat(sorted_items[start]["registered_at"])
            group = []
            for item in sorted_items[start:]:
                registered_at = datetime.fromisoformat(item["registered_at"])
                if registered_at - first > timedelta(minutes=60):
                    break
                group.append(item)
            if len(group) >= 3:
                groups.append(
                    PgpGroup(
                        group_id=f"PGP-{node_id}-{group_index:02d}",
                        access_node_id=node_id,
                        order_ids=[item["order_id"] for item in group],
                        detected_at=now,
                        action="TRANSFER_TO_STATION",
                        comment=f"ПГП на {node_id}: {len(group)} нарядов за 60 мин",
                    )
                )
                group_index += 1
                start += len(group)
            else:
                start += 1
    return groups
