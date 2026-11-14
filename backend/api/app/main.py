from fastapi import FastAPI
from pydantic import BaseModel
from api.app.models import DayInput, Staff, TravelMatrix, Plan, WorkType
from solver.app.vrp import solve_vrp

app = FastAPI(title="Solver Service")

class SolveRequest(BaseModel):
    day: DayInput
    staff: list[Staff]
    matrix: TravelMatrix
    work_types: list[WorkType]

@app.post("/solve", response_model=Plan)
async def solve(request: SolveRequest):
    plan = solve_vrp(request.day, request.staff, request.matrix, request.work_types)
    return plan