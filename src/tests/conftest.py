import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from httpx import AsyncClient
import app.api.v1.endpoints.packages
from app.main import app
from app.core.database import Base, get_db
import app.core.database as dbmod
from app.config.settings import Settings
from app.models.package import PackageType
from app.main import app

TEST_DATABASE_URL = "mysql+aiomysql://user:password@localhost:3306/delivery_test_db"

@pytest_asyncio.fixture(autouse=True)
def patch_session_service(monkeypatch):
    from app.main import app
    app.dependency_overrides[get_session_service] = lambda: TestSessionServiceMock()
    monkeypatch.setattr("app.core.session.get_session_service", lambda: TestSessionServiceMock())

@pytest_asyncio.fixture
async def mock_redis():
    class MockRedis:
        def __init__(self):
            self._data = {}
        async def get(self, key):
            return self._data.get(key)
        async def set(self, key, value, expire=None):
            self._data[key] = value
            return True
        async def delete(self, key):
            if key in self._data:
                del self._data[key]
            return True
        async def exists(self, key):
            return key in self._data
    return MockRedis()

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

class TestSessionServiceMock:
    async def get_or_create_session(self, request):
        return "test-session"
    def set_session_cookie(self, response, session_id):
        pass
    async def _create_session(self, session_id):
        pass
    async def _validate_session(self, session_id):
        return True
    async def invalidate_session(self, session_id):
        return
    session_ttl = 3600

from app.core.session import get_session_service
app.dependency_overrides[get_session_service] = lambda: TestSessionServiceMock()

@pytest_asyncio.fixture(scope="function")
async def test_db(monkeypatch):
    test_settings = Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        REDIS_URL="redis://localhost:6379/1",
        DEBUG=True,
        LOG_LEVEL="DEBUG"
    )
    monkeypatch.setattr("app.config.settings.get_settings", lambda: test_settings)
    monkeypatch.setattr("app.core.database.get_settings", lambda: test_settings)
    monkeypatch.setattr("app.main.settings", test_settings)
    monkeypatch.setattr("app.core.logging.settings", test_settings)
    monkeypatch.setattr("app.core.cache.settings", test_settings)
    monkeypatch.setattr("app.services.currency_service.settings", test_settings)

    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(dbmod, "engine", test_engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSessionLocal)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest_asyncio.fixture
async def client(test_db):
    async def override_get_db():
        yield test_db
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://testserver", cookies={"session_id": "test-session"}) as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def sample_package_data():
    return {
        "name": "Test Package",
        "weight": 2.5,
        "package_type": "clothes",
        "content_value": 100.0
    }

@pytest.fixture
def sample_package_types():
    return [
        {"id": 1, "name": "clothes", "description": "Одежда"},
        {"id": 2, "name": "electronics", "description": "Электроника"},
        {"id": 3, "name": "other", "description": "Разное"}
    ]

@pytest_asyncio.fixture
async def clothes_type(test_db):
    result = await test_db.execute(select(PackageType).where(PackageType.name == "clothes"))
    clothes = result.scalar_one_or_none()
    if not clothes:
        clothes = PackageType(name="clothes", description="Одежда")
        test_db.add(clothes)
        await test_db.commit()
        await test_db.refresh(clothes)
    return clothes

@pytest_asyncio.fixture
async def package_type(test_db):
    async def _inner(name, desc):
        result = await test_db.execute(select(PackageType).where(PackageType.name == name))
        t = result.scalar_one_or_none()
        if not t:
            t = PackageType(name=name, description=desc)
            test_db.add(t)
            await test_db.commit()
            await test_db.refresh(t)
        return t
    return _inner