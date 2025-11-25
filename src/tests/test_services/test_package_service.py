import pytest
from sqlalchemy import select
from app.services.package_service import PackageService
from app.models.package import Package, PackageType
from app.schemas.package import PackageCreate, PackageTypeEnum, PackageFilter

pytestmark = pytest.mark.asyncio

class TestPackageService:
    @pytest.mark.asyncio
    async def test_create_package(self, test_db, clothes_type):
        service = PackageService(test_db)
        package_data = PackageCreate(
            name="Test Package",
            weight=2.5,
            package_type=PackageTypeEnum.CLOTHES,
            content_value=100.0
        )
        package_id = await service.create_package("test-session", package_data)
        assert package_id is not None
        result = await test_db.execute(select(Package).where(Package.id == package_id))
        package = result.scalar_one()
        assert package.package_type_id == clothes_type.id

    
    @pytest.mark.asyncio
    async def test_get_packages_with_pagination(self, test_db, clothes_type):
        package_type_id = clothes_type.id
        packages = [
            Package(session_id="session-1", name="Package 1", weight=1.0, content_value=50.0, package_type_id=package_type_id),
            Package(session_id="session-1", name="Package 2", weight=2.0, content_value=100.0, package_type_id=package_type_id),
            Package(session_id="session-2", name="Package 3", weight=3.0, content_value=150.0, package_type_id=package_type_id)
        ]
        test_db.add_all(packages)
        await test_db.commit()

        service = PackageService(test_db)
        
        filters = PackageFilter(page=1, size=10)
        result = await service.get_user_packages("session-1", filters)
        
        assert result.total == 2
        assert len(result.packages) == 2
        assert all(pkg.session_id == "session-1" for pkg in result.packages)
    
    async def test_get_packages_for_calculation(self, test_db):
        package_type = PackageType(name="clothes", description="Одежда")
        test_db.add(package_type)
        await test_db.commit()
        
        packages = [
            Package(
                session_id="session-1",
                name="Not Calculated",
                weight=1.0,
                content_value=50.0,
                package_type_id=package_type.id,
                calculated=False
            ),
            Package(
                session_id="session-1",
                name="Calculated",
                weight=2.0, 
                content_value=100.0,
                package_type_id=package_type.id,
                calculated=True,
                delivery_cost=150.0
            )
        ]
        test_db.add_all(packages)
        await test_db.commit()
        
        service = PackageService(test_db)
        
        packages_for_calc = await service.get_packages_for_calculation()
        
        assert len(packages_for_calc) == 1
        assert packages_for_calc[0].name == "Not Calculated"
        assert packages_for_calc[0].calculated is False