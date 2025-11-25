import pytest
from unittest.mock import Mock, patch
from app.services.currency_service import CurrencyService


class TestCurrencyService:
    @pytest.mark.asyncio
    async def test_get_usd_rate_success(self, mock_redis):

        mock_response = Mock()
        mock_response.json.return_value = {
            "Valute": {
                "USD": {
                    "Value": 75.5
                }
            }
        }
        mock_response.raise_for_status = Mock()
        
        async def mock_get(*args, **kwargs):
            return mock_response
        
        with patch("httpx.AsyncClient.get", new=mock_get):
            service = CurrencyService()
            service.cache = mock_redis
            
            rate = await service.get_usd_rate()
            
            assert rate == 75.5
            assert mock_redis._data.get("usd_rub_rate") == "75.5"
    
    @pytest.mark.asyncio 
    async def test_get_usd_rate_from_cache(self, mock_redis):
        mock_redis._data["usd_rub_rate"] = "80.0"
        
        service = CurrencyService()
        service.cache = mock_redis
        
        rate = await service.get_usd_rate()
        
        assert rate == 80.0
    
    @pytest.mark.asyncio
    async def test_get_usd_rate_api_error(self, mock_redis):
        async def mock_get(*args, **kwargs):
            raise Exception("API Error")
        
        with patch("httpx.AsyncClient.get", new=mock_get):
            
            service = CurrencyService()
            service.cache = mock_redis
            
            rate = await service.get_usd_rate()
            
            assert rate is None