import httpx
from typing import Optional

from app.core.cache import Cache
from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

class CurrencyService:
    def __init__(self):
        self.cache = Cache()
        self.api_url = settings.CURRENCY_API_URL
    
    async def get_usd_rate(self) -> Optional[float]:
        try:
            cached_rate = await self.cache.get("usd_rub_rate")
            if cached_rate:
                logger.debug("USD rate retrieved from cache")
                return float(cached_rate)
            
            rate = await self._fetch_usd_rate()
            if rate:
                await self.cache.set(
                    "usd_rub_rate", 
                    str(rate), 
                    expire=settings.CURRENCY_CACHE_TTL
                )
                logger.info(f"USD rate updated: {rate}")
            
            return rate
            
        except Exception as e:
            logger.error(f"Error getting USD rate: {str(e)}")
            return None
    
    async def _fetch_usd_rate(self) -> Optional[float]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.api_url, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                usd_rate = data["Valute"]["USD"]["Value"]
                
                logger.debug(f"USD rate fetched from API: {usd_rate}")
                return float(usd_rate)
                
        except httpx.RequestError as e:
            logger.error(f"Request error fetching USD rate: {str(e)}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Data parsing error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching USD rate: {str(e)}")
            return None

_currency_service = None

async def get_currency_service() -> CurrencyService:
    global _currency_service
    if _currency_service is None:
        _currency_service = CurrencyService()
    return _currency_service