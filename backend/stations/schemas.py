from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class StationIn(BaseModel):
    name: str = Field(..., max_length=100, description='服务点名')
    floor: int = Field(..., description='楼层')
    location: str = Field(..., max_length=255, description='位置描述')
    safety_stock: int = Field(5, description='安全保有量')
    is_active: bool = Field(True, description='是否启用')


class StationOut(BaseModel):
    id: int
    name: str
    floor: int
    location: str
    safety_stock: int
    is_active: bool
    current_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
