import uuid

from fastapi import Request, Response

from app.core.cache import Cache
from app.core.logging import get_logger

logger = get_logger(__name__)

class SessionService:
    def __init__(self):
        self.cache = Cache()
        self.session_ttl = 3600

    async def get_or_create_session(self, request: Request) -> str:
        try:
            session_id = request.cookies.get("session_id")

            if not session_id:
                session_id = str(uuid.uuid4())
                await self._create_session(session_id)
                logger.info("New session created", extra={"session_id": session_id})
            elif not await self._validate_session(session_id):
                session_id = str(uuid.uuid4())
                await self._create_session(session_id)
                logger.info("Session re-created (old invalid)", extra={"session_id": session_id})

            return session_id
        except Exception as e:
            logger.error(f"Error managing session: {str(e)}")
            session_id = str(uuid.uuid4())
            await self._create_session(session_id)
            return session_id

    def set_session_cookie(self, response: Response, session_id: str) -> None:
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=self.session_ttl,
            httponly=True,
            samesite="lax"
        )

    async def _create_session(self, session_id: str) -> None:
        await self.cache.set(
            f"session:{session_id}",
            "active",
            expire=self.session_ttl
        )

    async def _validate_session(self, session_id: str) -> bool:
        try:
            session_data = await self.cache.get(f"session:{session_id}")
            return session_data is not None
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return False

    async def invalidate_session(self, session_id: str) -> None:
        try:
            await self.cache.delete(f"session:{session_id}")
            logger.info("Session invalidated", extra={"session_id": session_id})
        except Exception as e:
            logger.error(f"Error invalidating session: {str(e)}")

def get_session_service():
    return SessionService()