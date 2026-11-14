import httpx
from api.app.models import DayInput, Staff, TravelMatrix, Plan, WorkType

SOLVER_URL = "http://127.0.0.1:8081"

async def request_solver(day: DayInput, staff: list[Staff], matrix: TravelMatrix, work_types: list[WorkType]) -> Plan:
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "day": day.model_dump(mode="json"),
            "staff": [s.model_dump(mode="json") for s in staff],
            "matrix": matrix.model_dump(mode="json"),
            "work_types": [w.model_dump(mode="json") for w in work_types]
        }
        resp = await client.post(f"{SOLVER_URL}/solve", json=payload)
        resp.raise_for_status()
        return Plan.model_validate(resp.json())