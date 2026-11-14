from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from api.app.models import DayInput, Staff, TravelMatrix, Plan, WorkType, ServiceCenter
from solver.app.vrp import solve_vrp
import traceback

app = FastAPI(title="Solver Service")

class SolveRequest(BaseModel):
    date: str
    day: DayInput
    orders: list[dict]
    staff: list[Staff]
    matrix: TravelMatrix
    work_types: list[WorkType]
    service_centers: list[ServiceCenter]

@app.post("/solve", response_model=Plan)
async def solve(request: SolveRequest):
    try:
        return solve_vrp(
            date=request.date,
            day=request.day,
            orders=request.orders,
            staff=request.staff,
            work_types=request.work_types,
            service_centers=request.service_centers,
            matrix=request.matrix,
        )
    except Exception as e:
        error_trace = traceback.format_exc()
        print("\n" + "="*50)
        print("ОШИБКА В СОЛВЕРЕ:")
        print(error_trace)
        print("="*50 + "\n")
        raise HTTPException(status_code=500, detail=str(e))