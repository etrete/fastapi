from typing import List
from app.models.package import Package
from app.services.currency_service import get_currency_service
from app.core.logging import get_logger

logger = get_logger(__name__)

class DeliveryCalculator:
    
    @staticmethod
    async def calculate_delivery_cost(weight: float, content_value: float) -> float:
        try:
            currency_service = await get_currency_service()
            usd_rate = await currency_service.get_usd_rate()
            
            if not usd_rate:
                logger.error("Cannot calculate delivery cost: USD rate not available")
                return 0.0
            
            delivery_cost = (weight * 0.5 + content_value * 0.01) * usd_rate
            
            delivery_cost = round(delivery_cost, 2)
            
            logger.debug("Delivery cost calculated", 
                        extra={"weight": weight, "content_value": content_value, 
                               "usd_rate": usd_rate, "delivery_cost": delivery_cost})
            
            return delivery_cost
            
        except Exception as e:
            logger.error(f"Error calculating delivery cost: {str(e)}")
            return 0.0
    
    @staticmethod
    async def calculate_packages_delivery_cost(packages: List[Package]) -> List[dict]:
        results = []
        
        for package in packages:
            try:
                delivery_cost = await DeliveryCalculator.calculate_delivery_cost(
                    package.weight, package.content_value
                )
                
                results.append({
                    "package_id": package.id,
                    "delivery_cost": delivery_cost,
                    "success": True
                })
                
            except Exception as e:
                logger.error(f"Error calculating delivery cost for package {package.id}: {str(e)}")
                results.append({
                    "package_id": package.id,
                    "delivery_cost": 0.0,
                    "success": False,
                    "error": str(e)
                })
        
        return results