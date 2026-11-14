import json, httpx
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

ref = {
    "service_centers": json.loads((DATA / "service_centers.json").read_text(encoding="utf-8")),
    "staff":           json.loads((DATA / "staff.json").read_text(encoding="utf-8")),
    "access_nodes":    json.loads((DATA / "access_nodes.json").read_text(encoding="utf-8")),
    "work_types":      json.loads((DATA / "work_types.json").read_text(encoding="utf-8")),
}
matrix = json.loads((DATA / "travel_matrix.json").read_text(encoding="utf-8"))

BASE = "http://127.0.0.1:8000/api/v1"

r = httpx.put(f"{BASE}/reference", json=ref, timeout=120)
r.raise_for_status()
print("reference:", r.json())

r = httpx.put(f"{BASE}/reference/travel-matrix", json=matrix, timeout=120)
r.raise_for_status()
print("matrix:", r.json())