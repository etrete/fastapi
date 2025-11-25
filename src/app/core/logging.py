import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
from datetime import datetime
from app.config.settings import get_settings

settings = get_settings()

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging() -> logging.Logger:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    logger.handlers.clear()
    
    formatter = JSONFormatter()
    
    file_handler = RotatingFileHandler(
        filename=log_dir / "delivery_service.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"app.{name}")
    return logger

root_logger = setup_logging()