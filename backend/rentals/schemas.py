from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BorrowIn(BaseModel):
    cart_id: int = Field(..., description='推车ID')
    user_phone: str = Field(..., max_length=20, description='借用人手机号')
    borrow_station_id: int = Field(..., description='借出服务点ID')


class ReturnIn(BaseModel):
    rental_no: str = Field(..., max_length=50, description='借用单号')
    return_station_id: int = Field(..., description='归还服务点ID')


class RentalOut(BaseModel):
    id: int
    rental_no: str
    user_phone: str
    borrow_time: datetime
    return_time: Optional[datetime] = None
    borrow_station_id: int
    borrow_station_name: str
    return_station_id: Optional[int] = None
    return_station_name: Optional[str] = None
    cart_id: int
    cart_no: str
    stage: str
    stage_display: str
    is_overdue: bool = False

    class Config:
        from_attributes = True
