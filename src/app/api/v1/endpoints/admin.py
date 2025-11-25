from fastapi import APIRouter, HTTPException, status

from app.tasks.delivery_calculation import run_calculation_once
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post(
    "/calculate-delivery",
    summary="Запустить расчет стоимости доставки",
    description="Запускает немедленный расчет стоимости доставки для всех необработанных посылок",
    status_code=status.HTTP_200_OK
)
async def calculate_delivery():
    try:
        result = await run_calculation_once()

        if "error" in result:
            logger.error("Calculation error", extra={"details": result})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        logger.info("Manual delivery calculation completed", extra={"result": result})
        return result

    except Exception as e:
        logger.error(f"Error in manual calculation: {str(e)}", extra={"details": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )