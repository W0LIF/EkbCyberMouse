from fastapi import APIRouter
from api.app.models import ReferenceData, TravelMatrix, LoadResult
from api.app.services.matrix_store import matrix_store
from api.app.services import state

router = APIRouter(tags=["reference"])

@router.put("/reference", response_model=LoadResult)
async def put_reference(data: ReferenceData):
    state.CURRENT_REFERENCE = data
    print(f"✅ Получено СЦ: {len(data.service_centers)}, Сотрудников: {len(data.staff)}")
    return {"status": "loaded", "counts": {"staff": len(data.staff), "nodes": len(data.access_nodes)}}

@router.put("/reference/travel-matrix", response_model=LoadResult)
async def put_matrix(matrix: TravelMatrix):
    matrix_store.store(matrix)
    print(f"✅ Матрица загружена. Точек: {len(matrix.points)}")
    return {"status": "loaded", "counts": {"points": len(matrix.points)}}