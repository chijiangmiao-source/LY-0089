from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StrandedReportIn(BaseModel):
    cart_id: int = Field(..., description='推车ID')
    report_station_id: int = Field(..., description='上报服务点ID')
    reporter_name: Optional[str] = Field(None, max_length=50, description='上报人姓名')
    reporter_phone: Optional[str] = Field(None, max_length=20, description='上报人电话')
    description: Optional[str] = Field(None, description='情况描述')


class StrandedOut(BaseModel):
    id: int
    cart_id: int
    cart_no: str
    report_station_id: int
    report_station_name: str
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    description: Optional[str] = None
    status: str
    status_display: str
    reported_at: datetime
    recycled_at: Optional[datetime] = None
    duration_hours: float

    class Config:
        from_attributes = True
