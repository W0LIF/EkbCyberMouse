from fastapi import APIRouter, HTTPException
from api.app.models import Plan, DayInput, LoadResult
from api.app.services.solver_client import request_solver
from api.app.services.matrix_store import matrix_store
from api.app.services import state

router = APIRouter(tags=["plan"])

@router.put("/days/{date}", response_model=LoadResult)
async def put_day(date: str, day: DayInput):
    state.CURRENT_DAY = day
    state.CURRENT_PLAN = None
    return {"status": "loaded", "counts": {"orders": len(day.orders)}}

@router.post("/days/{date}/plan", response_model=Plan)
async def build_plan(date: str):
    if not state.CURRENT_DAY or not matrix_store.matrix or not state.CURRENT_REFERENCE:
        raise HTTPException(status_code=404, detail="Не хватает данных (день, матрица или справочники)")
    
    plan = await request_solver(
        state.CURRENT_DAY, 
        state.CURRENT_REFERENCE.staff, 
        matrix_store.matrix, 
        state.CURRENT_REFERENCE.work_types
    )
    state.CURRENT_PLAN = plan
    return plan

@router.get("/days/{date}/plan", response_model=Plan)
async def get_plan(date: str):
    if not state.CURRENT_PLAN:
        raise HTTPException(status_code=404, detail="План еще не построен")
    return state.CURRENT_PLAN