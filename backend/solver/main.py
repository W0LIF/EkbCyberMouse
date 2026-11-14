from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from api.app.models import DayInput, Staff, TravelMatrix, Plan, WorkType, ServiceCenter
from solver.app.vrp import solve_vrp
import traceback

app = FastAPI(title="Solver Service")


class SolveRequest(BaseModel):
    date: str
    day: DayInput
    staff: list[Staff]
    matrix: TravelMatrix
    work_types: list[WorkType]
    service_centers: list[ServiceCenter]
    plan_version: int = 1


@app.post("/solve", response_model=Plan)
async def solve(request: SolveRequest):
    try:
        return solve_vrp(
            date=request.date,
            day=request.day,
            orders=request.day.orders,
            staff=request.staff,
            work_types=request.work_types,
            service_centers=request.service_centers,
            matrix=request.matrix,
            plan_version=request.plan_version,
            max_runtime_seconds=30,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))