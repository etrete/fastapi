from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.logging import setup_logging
from app.core.database import init_db
from app.core.session import get_session_service
from app.api.v1.endpoints import packages, package_types, admin
from app.config.settings import get_settings

settings = get_settings()
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting delivery service application")
    await init_db()
    
    yield
    
    logger.info("Stopping delivery service application")

app = FastAPI(
    title="Delivery Service API",
    description="Микросервис для расчета стоимости доставки посылок",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

@app.middleware("http")
async def session_middleware(request: Request, call_next):
    session_service = get_session_service()
    response = Response()
    try:
        session_id = await session_service.get_or_create_session(request)
        session_service.set_session_cookie(response, session_id)
        request.state.session_id = session_id
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Session middleware error: {str(e)}")
        response = Response(
            content='{"detail": "Internal server error"}',
            status_code=500,
            media_type="application/json"
        )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(packages.router, prefix="/api/v1/packages", tags=["packages"])
app.include_router(package_types.router, prefix="/api/v1/package-types", tags=["package-types"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "delivery-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        reload=settings.DEBUG
    )