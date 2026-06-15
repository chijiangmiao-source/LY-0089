from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MaintenanceCreateIn(BaseModel):
    cart_id: int = Field(..., description='推车ID')
    fault_type: str = Field(..., description='故障类型')
    report_station_id: int = Field(..., description='报修服务点ID')
    reporter_name: Optional[str] = Field(None, max_length=50, description='报修人姓名')
    description: Optional[str] = Field(None, description='故障描述')


class MaintenanceUpdateIn(BaseModel):
    repair_result: Optional[str] = Field(None, description='维修结果')


class MaintenanceOut(BaseModel):
    id: int
    cart_id: int
    cart_no: str
    fault_type: str
    fault_type_display: str
    report_station_id: int
    report_station_name: str
    reporter_name: Optional[str] = None
    description: Optional[str] = None
    status: str
    status_display: str
    repair_result: Optional[str] = None
    reported_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
