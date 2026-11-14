from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from api.app.models import DayInput, Staff, TravelMatrix, Plan, WorkType
from solver.app.vrp import solve_vrp
import traceback

app = FastAPI(title="Solver Service")

class SolveRequest(BaseModel):
    day: DayInput
    staff: list[Staff]
    matrix: TravelMatrix
    work_types: list[WorkType]

@app.post("/solve", response_model=Plan)
async def solve(request: SolveRequest):
    try:
        return solve_vrp(request.day, request.staff, request.matrix, request.work_types)
    except Exception as e:
        error_trace = traceback.format_exc()
        print("\n" + "="*50)
        print("ОШИБКА В СОЛВЕРЕ:")
        print(error_trace)
        print("="*50 + "\n")
        raise HTTPException(status_code=500, detail=str(e))