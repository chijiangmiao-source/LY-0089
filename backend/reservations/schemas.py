from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReservationCreateIn(BaseModel):
    user_phone: str = Field(..., max_length=20, description='预约人手机号')
    station_id: int = Field(..., description='预约服务点ID')
    cart_type: Optional[str] = Field(None, description='车型偏好: standard/large')


class ReservationOut(BaseModel):
    id: int
    reservation_no: str
    user_phone: str
    station_id: int
    station_name: str
    cart_id: Optional[int] = None
    cart_no: Optional[str] = None
    reserve_time: datetime
    expire_time: datetime
    pickup_time: Optional[datetime] = None
    status: str
    status_display: str
    is_expired: bool

    class Config:
        from_attributes = True


class ReservationPickupIn(BaseModel):
    reservation_no: str = Field(..., max_length=50, description='预约单号')
    cart_id: int = Field(..., description='取车ID')
    borrow_station_id: int = Field(..., description='借出服务点ID')
