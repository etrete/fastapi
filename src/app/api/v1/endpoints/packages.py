from fastapi import APIRouter, Depends, HTTPException, status, Request, Response

from app.schemas.package import (
    PackageCreate, 
    PackageResponse, 
    PackageListResponse,
    PackageFilter
)
from app.services.package_service import PackageService, get_package_service
from app.core.session import get_session_service, SessionService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/debug/headers", include_in_schema=False)
async def debug_headers(request: Request):
    return {
        "url": str(request.url),
        "user_agent": request.headers.get("user-agent"),
        "referer": request.headers.get("referer"),
        "headers": dict(request.headers)
    }


@router.get("/debug/session", include_in_schema=False)
async def debug_session(request: Request, session_service: SessionService = Depends(get_session_service)):
    session_id = await session_service.get_or_create_session(request)
    return {
        "session_id": session_id,
        "is_swagger": "swagger" in str(request.url) or "docs" in str(request.url),
        "url": str(request.url)
    }


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать посылку",
    description="Регистрирует новую посылку и возвращает её ID"
)
async def create_package(
    request: Request,
    response: Response,
    package_data: PackageCreate,
    package_service: PackageService = Depends(get_package_service),
    session_service: SessionService = Depends(get_session_service)
):
    try:
        session_id = await session_service.get_or_create_session(request)
        session_service.set_session_cookie(response, session_id)
        package_id = await package_service.create_package(session_id, package_data)
        logger.info("Package created successfully", extra={"package_id": package_id, "session_id": session_id})
        return {"package_id": package_id, "message": "Package registered successfully"}
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating package: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/",
    response_model=PackageListResponse,
    summary="Получить список посылок",
    description="Возвращает список посылок пользователя с пагинацией и фильтрацией"
)
async def get_packages(
    request: Request,
    response: Response,
    filters: PackageFilter = Depends(),
    package_service: PackageService = Depends(get_package_service),
    session_service: SessionService = Depends(get_session_service)
):
    try:
        session_id = await session_service.get_or_create_session(request)
        session_service.set_session_cookie(response, session_id)
        result = await package_service.get_user_packages(session_id, filters)
        logger.info(f"Packages retrieved successfully", extra={"session_id": session_id, "count": len(result.packages)})
        return result
    except Exception as e:
        logger.error(f"Error retrieving packages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{package_id}", response_model=PackageResponse)
async def get_package_by_id(
    package_id: int,
    package_service: PackageService = Depends(get_package_service)
):
    try:
        logger.info(f"Fetching package id={package_id} by direct ID lookup (no session check)")
        package = await package_service.get_package_by_id(package_id)
        if not package:
            logger.warning(f"Package not found: id={package_id}")
            raise HTTPException(status_code=404, detail="Package not found")
        return package
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_package_by_id: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")