import asyncio
import signal

from app.services.package_service import PackageService
from app.services.delivery_calculator import DeliveryCalculator
from app.core.database import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

class DeliveryCalculationTask:
    def __init__(self):
        self.running = False
        self.interval = 300

    async def start(self):
        self.running = True
        logger.info("Starting delivery calculation task")

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        while self.running:
            try:
                await self._run_calculation()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in delivery calculation task: {str(e)}")
                await asyncio.sleep(60)

    async def _run_calculation(self):
        try:
            logger.info("Running delivery cost calculation")

            async with SessionLocal() as db:
                package_service = PackageService(db)
                packages = await package_service.get_packages_for_calculation(limit=1000)

                if not packages:
                    logger.info("No packages need delivery cost calculation")
                    return

                logger.info(f"Calculating delivery cost for {len(packages)} packages")

                results = await DeliveryCalculator.calculate_packages_delivery_cost(packages)

                successful_updates = 0
                for result in results:
                    if result["success"]:
                        await package_service.update_delivery_cost(
                            result["package_id"], result["delivery_cost"]
                        )
                        successful_updates += 1

                logger.info(
                    "Delivery cost calculation completed",
                    extra={"total": len(packages), "successful": successful_updates}
                )

        except Exception as e:
            logger.error(f"Error running delivery calculation: {str(e)}")
            raise

    async def run_once(self):
        try:
            logger.info("Running one-time delivery calculation")
            async with SessionLocal() as db:
                package_service = PackageService(db)
                packages = await package_service.get_packages_for_calculation(limit=1000)

                if not packages:
                    return {"message": "No packages need calculation", "processed": 0}

                results = await DeliveryCalculator.calculate_packages_delivery_cost(packages)

                successful_updates = 0
                for result in results:
                    if result["success"]:
                        await package_service.update_delivery_cost(
                            result["package_id"], result["delivery_cost"]
                        )
                        successful_updates += 1

                return {
                    "message": "Calculation completed",
                    "total_packages": len(packages),
                    "successful_updates": successful_updates
                }

        except Exception as e:
            logger.error(f"Error in one-time calculation: {str(e)}")
            return {"error": str(e)}

    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, stopping task")
        self.running = False

_calculation_task = None

async def start_periodic_tasks():
    global _calculation_task
    if _calculation_task is None:
        _calculation_task = DeliveryCalculationTask()
        asyncio.create_task(_calculation_task.start())

async def run_calculation_once() -> dict:
    global _calculation_task
    if _calculation_task is None:
        _calculation_task = DeliveryCalculationTask()
    return await _calculation_task.run_once()