from fastapi import APIRouter, HTTPException
from api.app.models import Plan, DayInput, Staff, TravelMatrix, WorkType, ReferenceData
from api.app.services.solver_client import request_solver

router = APIRouter(tags=["plan"])

# Временное хранилище
CURRENT_DAY: DayInput | None = None
CURRENT_PLAN: Plan | None = None
CURRENT_STAFF: list[Staff] = []
CURRENT_MATRIX: TravelMatrix | None = None
CURRENT_WORK_TYPES: list[WorkType] = []

# Вспомогательный эндпоинт для сохранения в память (пока Аня не сделала БД)
@router.put("/internal/reference", response_model=dict)
async def save_ref(data: ReferenceData):
    global CURRENT_STAFF, CURRENT_WORK_TYPES
    CURRENT_STAFF = data.staff
    CURRENT_WORK_TYPES = data.work_types
    return {"status": "loaded"}

@router.put("/internal/matrix", response_model=dict)
async def save_matrix(matrix: TravelMatrix):
    global CURRENT_MATRIX
    CURRENT_MATRIX = matrix
    return {"status": "loaded"}

@router.put("/days/{date}", response_model=dict)
async def put_day(date: str, day: DayInput):
    global CURRENT_DAY, CURRENT_PLAN
    CURRENT_DAY = day
    CURRENT_PLAN = None
    return {"status": "loaded", "counts": {"orders": len(day.orders)}}

@router.post("/days/{date}/plan", response_model=Plan)
async def build_plan(date: str):
    global CURRENT_PLAN
    if not CURRENT_DAY or not CURRENT_MATRIX or not CURRENT_STAFF:
        raise HTTPException(status_code=404, detail="Не хватает данных (день, матрица или сотрудники)")
    
    # Вызов солвера
    plan = await request_solver(CURRENT_DAY, CURRENT_STAFF, CURRENT_MATRIX, CURRENT_WORK_TYPES)
    CURRENT_PLAN = plan
    return plan

@router.get("/days/{date}/plan", response_model=Plan)
async def get_plan(date: str):
    if not CURRENT_PLAN:
        raise HTTPException(status_code=404, detail="План еще не построен")
    return CURRENT_PLAN