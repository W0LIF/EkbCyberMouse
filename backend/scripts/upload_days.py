import json, httpx
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
orders = json.loads((DATA / "orders.json").read_text(encoding="utf-8"))

BASE = "http://127.0.0.1:8000/api/v1"

for d in ["2026-11-14", "2026-11-15", "2026-11-16", "2026-11-17", "2026-11-18"]:
    date_compact = d.replace("-", "")
    day_orders = [o for o in orders if f"-{date_compact}-" in o["order_id"]]
    body = {
        "date": d,
        "now": f"{d}T08:00:00+05:00",
        "orders": day_orders,
        "absent_staff_ids": [],
    }
    r = httpx.put(f"{BASE}/days/{d}", json=body, timeout=120)
    print(d, r.status_code, r.json() if r.status_code < 500 else r.text[:300])