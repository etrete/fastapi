from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class PackageType(Base):
    """Тип посылки."""
    
    __tablename__ = "package_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    
    
    packages = relationship("Package", back_populates="package_type")

class Package(Base):
    """Посылка."""
    
    __tablename__ = "packages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)  # Идентификатор сессии пользователя
    name = Column(String(255), nullable=False)
    weight = Column(Float, nullable=False)
    content_value = Column(Float, nullable=False)
    delivery_cost = Column(Float, nullable=True)
    calculated = Column(Boolean, default=False)
    
    package_type_id = Column(Integer, ForeignKey("package_types.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    package_type = relationship("PackageType", back_populates="packages")