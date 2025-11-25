from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.package import Package, PackageType
from app.schemas.package import PackageCreate, PackageResponse, PackageListResponse, PackageFilter
from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)

class PackageService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_package(self, session_id: str, package_data: PackageCreate) -> int:
        try:
            package_type = await self._get_package_type_by_name(package_data.package_type.value)
            if not package_type:
                raise ValueError(f"Package type {package_data.package_type} not found")
            package = Package(
                session_id=session_id,
                name=package_data.name,
                weight=package_data.weight,
                content_value=package_data.content_value,
                package_type_id=package_type.id
            )
            self.db.add(package)
            await self.db.commit()
            await self.db.refresh(package)

            logger.info("Package created", extra={"package_id": package.id, "session_id": session_id})
            return package.id

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating package: {str(e)}")
            raise

    async def get_user_packages(self, session_id: str, filters: PackageFilter) -> PackageListResponse:
        try:
            query = select(Package).options(selectinload(Package.package_type)).where(Package.session_id == session_id)

            if filters.package_type is not None:
                type_name = getattr(filters.package_type, "value", filters.package_type)
                package_type = await self._get_package_type_by_name(type_name)
                if package_type:
                    query = query.where(Package.package_type_id == package_type.id)

            if filters.calculated is not None:
                query = query.where(Package.calculated == filters.calculated)

            if hasattr(filters, "hasdeliverycost") and filters.hasdeliverycost is not None:
                if str(filters.hasdeliverycost).lower() == "true":
                    query = query.where(Package.delivery_cost.isnot(None))
                elif str(filters.hasdeliverycost).lower() == "false":
                    query = query.where(Package.delivery_cost.is_(None))

            from sqlalchemy import func
            total_subquery = query.subquery()
            total_query = select(func.count()).select_from(total_subquery)
            total_result = await self.db.execute(total_query)
            total = total_result.scalar_one()
            offset = (filters.page - 1) * filters.size
            query = query.offset(offset).limit(filters.size)

            result = await self.db.execute(query)
            packages = result.scalars().all()
            package_responses = [
                PackageResponse(
                    id=pkg.id,
                    session_id=pkg.session_id,
                    name=pkg.name,
                    weight=pkg.weight,
                    package_type=pkg.package_type.name,
                    content_value=pkg.content_value,
                    delivery_cost=pkg.delivery_cost,
                    calculated=pkg.calculated,
                    created_at=pkg.created_at,
                    updated_at=pkg.updated_at
                )
                for pkg in packages
            ]
            return PackageListResponse(
                packages=package_responses,
                total=total,
                page=filters.page,
                size=filters.size,
                has_next=(filters.page * filters.size) < total
            )
        except Exception as e:
            logger.error(f"Error getting user packages: {str(e)}")
            raise

    async def get_package_by_id(self, package_id: int) -> Optional[PackageResponse]:
        try:
            logger.info(f"🔍 Searching for package by ID only: package_id={package_id}")
            from sqlalchemy.orm import selectinload
            query = select(Package).options(selectinload(Package.package_type)).where(Package.id == package_id)
            result = await self.db.execute(query)
            package = result.scalar_one_or_none()
            if package:
                logger.info(f"✅ Package found: {package.id}")
                return PackageResponse(
                    id=package.id,
                    session_id=package.session_id,
                    name=package.name,
                    weight=package.weight,
                    package_type=package.package_type.name,
                    content_value=package.content_value,
                    delivery_cost=package.delivery_cost,
                    calculated=package.calculated,
                    created_at=package.created_at,
                    updated_at=package.updated_at
                )
            return None

        except Exception as e:
            logger.error(f"Error in get_package_by_id: {str(e)}")
            raise

    async def get_packages_for_calculation(self, limit: int = 1000) -> List[Package]:
        try:
            query = select(Package).where(
                Package.calculated == False
            ).limit(limit)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting packages for calculation: {str(e)}")
            raise

    async def update_delivery_cost(self, package_id: int, delivery_cost: float) -> None:
        try:
            query = select(Package).where(Package.id == package_id)
            result = await self.db.execute(query)
            package = result.scalar_one_or_none()
            if package:
                package.delivery_cost = delivery_cost
                package.calculated = True
                await self.db.commit()
                logger.info("Delivery cost updated", extra={"package_id": package_id, "delivery_cost": delivery_cost})
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating delivery cost: {str(e)}")
            raise

    async def _get_package_type_by_name(self, name: str) -> Optional[PackageType]:
        query = select(PackageType).where(PackageType.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

async def get_package_service() -> PackageService:
    async for db in get_db():
        yield PackageService(db)