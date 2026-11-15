from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.models import ReferenceData, TravelMatrix, LoadResult, ServiceCenter, Staff
from api.app.services.matrix_store import matrix_store
from api.app.repositories.db import get_db
from api.app.repositories.sql_reference_repo import SqlReferenceRepo

router = APIRouter(tags=["reference"])

@router.put("/reference", response_model=LoadResult)
async def put_reference(data: ReferenceData, db: AsyncSession = Depends(get_db)):
    # Сохраняем справочники в PostgreSQL
    repo = SqlReferenceRepo(db)
    await repo.replace_all(data)
    
    return {
        "status": "loaded",
        "counts": {
            "service_centers": len(data.service_centers),
            "staff": len(data.staff),
            "access_nodes": len(data.access_nodes),
            "buildings": sum(len(node.buildings) for node in data.access_nodes),
            "work_types": len(data.work_types),
        },
    }


@router.get("/reference/staff", response_model=list[Staff])
async def get_staff(db: AsyncSession = Depends(get_db)):
    return await SqlReferenceRepo(db).get_staff()


@router.get("/reference/service-centers", response_model=list[ServiceCenter])
async def get_service_centers(db: AsyncSession = Depends(get_db)):
    return await SqlReferenceRepo(db).get_service_centers()

@router.put("/reference/travel-matrix", response_model=LoadResult)
async def put_matrix(matrix: TravelMatrix):
    matrix_store.store(matrix)
    return {"status": "loaded", "counts": {"points": len(matrix.points)}}