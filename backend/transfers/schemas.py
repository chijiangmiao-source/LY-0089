from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TransferCreateIn(BaseModel):
    cart_id: int = Field(..., description='推车ID')
    from_station_id: int = Field(..., description='源站ID')
    to_station_id: int = Field(..., description='目标站ID')
    priority: Optional[str] = Field('normal', description='优先级: normal/urgent')


class TransferOut(BaseModel):
    id: int
    transfer_no: str
    cart_id: int
    cart_no: str
    from_station_id: int
    from_station_name: str
    to_station_id: int
    to_station_name: str
    status: str
    status_display: str
    priority: str
    priority_display: str
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
