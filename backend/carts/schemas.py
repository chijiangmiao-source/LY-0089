from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CartIn(BaseModel):
    cart_no: str = Field(..., max_length=50, description='推车编号')
    station_id: int = Field(..., description='所属服务点ID')
    cart_type: str = Field(..., description='车型: standard/large')
    status: str = Field(..., description='当前状态')
    last_clean_time: Optional[datetime] = Field(None, description='最近清洁时间')


class CartOut(BaseModel):
    id: int
    cart_no: str
    station_id: int
    station_name: str
    cart_type: str
    status: str
    status_display: str
    last_clean_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
