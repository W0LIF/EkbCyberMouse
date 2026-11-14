from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.models import ReferenceData, TravelMatrix, LoadResult
from api.app.services.matrix_store import matrix_store
from api.app.repositories.db import get_db
from api.app.repositories.sql_reference_repo import SqlReferenceRepo

router = APIRouter(tags=["reference"])

@router.put("/reference", response_model=LoadResult)
async def put_reference(data: ReferenceData, db: AsyncSession = Depends(get_db)):
    # Сохраняем справочники в PostgreSQL
    repo = SqlReferenceRepo(db)
    await repo.replace_all(data)
    
    print(f"✅ Справочники сохранены в БД: СЦ {len(data.service_centers)}, Сотрудников {len(data.staff)}")
    return {"status": "loaded", "counts": {"staff": len(data.staff), "nodes": len(data.access_nodes)}}

@router.put("/reference/travel-matrix", response_model=LoadResult)
async def put_matrix(matrix: TravelMatrix):
    # Матрицу оставляем в памяти (как договаривались)
    matrix_store.store(matrix)
    print(f"✅ Матрица загружена в память. Точек: {len(matrix.points)}")
    return {"status": "loaded", "counts": {"points": len(matrix.points)}}