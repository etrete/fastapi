import asyncio
import sys
from src.app.core.database import init_db
from src.app.core.logging import setup_logging

async def main():
    logger = setup_logging()
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())