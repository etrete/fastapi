from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from app.models.package import PackageType
from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

class PackageTypeResponse(BaseModel):
    id: int
    name: str
    description: str

@router.get(
    "/",
    response_model=List[PackageTypeResponse],
    summary="Получить все типы посылок",
    description="Возвращает список всех доступных типов посылок с их ID"
)
async def get_package_types(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(PackageType))
        package_types = result.scalars().all()
        logger.debug("Package types retrieved successfully", extra={"count": len(package_types)})
        return [PackageTypeResponse.model_validate(pt, from_attributes=True) for pt in package_types]
    except Exception as e:
        logger.error(f"Error retrieving package types: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")