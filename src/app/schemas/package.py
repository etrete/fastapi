from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PackageTypeEnum(str, Enum):
    CLOTHES = "clothes"
    ELECTRONICS = "electronics"
    OTHER = "other"

class PackageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Название посылки")
    weight: float = Field(..., gt=0, description="Вес в кг")
    package_type: PackageTypeEnum = Field(..., description="Тип посылки")
    content_value: float = Field(..., ge=0, description="Стоимость содержимого в USD")

    @field_validator('weight')
    def validate_weight(cls, v):
        if v > 1000:
            raise ValueError('Weight cannot exceed 1000 kg')
        return v

class PackageCreate(PackageBase):
    pass

class PackageResponse(PackageBase):
    id: int
    session_id: str
    delivery_cost: Optional[float] = None
    calculated: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PackageListResponse(BaseModel):
    packages: List[PackageResponse]
    total: int
    page: int
    size: int
    has_next: bool

class PackageFilter(BaseModel):
    package_type: Optional[PackageTypeEnum] = None
    calculated: Optional[bool] = None
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)