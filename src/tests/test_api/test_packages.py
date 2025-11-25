import pytest
from fastapi import status
from sqlalchemy import select
from app.models.package import Package, PackageType

pytestmark = pytest.mark.asyncio

class TestPackagesAPI:
    async def test_create_package_success(self, client, test_db, sample_package_data):
        package_types = [
            PackageType(name="clothes", description="Одежда"),
            PackageType(name="electronics", description="Электроника"),
            PackageType(name="other", description="Разное")
        ]
        test_db.add_all(package_types)
        await test_db.commit()

        response = await client.post("/api/v1/packages/", json=sample_package_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "package_id" in data
        assert "message" in data

        result = await test_db.execute(select(Package))
        packages = result.scalars().all()
        assert len(packages) == 1
        assert packages[0].name == sample_package_data["name"]
        assert packages[0].weight == sample_package_data["weight"]

    async def test_create_package_invalid_data(self, client):
        invalid_data = {
            "name": "",
            "weight": -1,
            "package_type": "invalid_type",
            "content_value": -100
        }
        response = await client.post("/api/v1/packages/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_get_packages_empty(self, client, test_db):
        response = await client.get("/api/v1/packages/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["packages"]) == 0
        assert data["page"] == 1
        assert data["size"] == 10
        assert data["has_next"] is False

    async def test_get_package_not_found(self, client):
        response = await client.get("/api/v1/packages/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_packages_with_pagination(self, client, test_db, sample_package_data, clothes_type):
        result = await test_db.execute(select(PackageType).where(PackageType.name == "clothes"))
        package_type = result.scalar_one()
        packages = [
            Package(
                session_id="test-session",
                name=f"Package {i}",
                weight=1.0 + i,
                content_value=10.0 * i,
                package_type_id=package_type.id
            ) for i in range(15)
        ]
        test_db.add_all(packages)
        await test_db.commit()

        client.cookies.set("session_id", "test-session")
        response = await client.get("/api/v1/packages/?page=1&size=5")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 15
        assert len(data["packages"]) == 5
        assert data["page"] == 1
        assert data["size"] == 5
        assert data["has_next"] is True

    async def test_get_packages_with_filters(self, client, test_db, package_type):
        clothes_type = await package_type("clothes", "Одежда")
        electronics_type = await package_type("electronics", "Электроника")
        packages = [
            Package(
                session_id="test-session",
                name="Clothes Package",
                weight=1.0,
                content_value=50.0,
                package_type_id=clothes_type.id,
                calculated=True,
                delivery_cost=100.0
            ),
            Package(
                session_id="test-session",
                name="Electronics Package",
                weight=2.0,
                content_value=200.0,
                package_type_id=electronics_type.id,
                calculated=False
            )
        ]
        test_db.add_all(packages)
        await test_db.commit()
        client.cookies.set("session_id", "test-session")
        response = await client.get("/api/v1/packages/?package_type=clothes")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["packages"][0]["name"] == "Clothes Package"

        response = await client.get("/api/v1/packages/?calculated=true")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["packages"][0]["calculated"] is True