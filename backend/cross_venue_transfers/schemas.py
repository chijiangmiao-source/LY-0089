from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class CrossVenueTransferCreateIn(BaseModel):
    from_venue_id: int = Field(..., description='申请场地ID')
    to_venue_id: int = Field(..., description='目标场地ID')
    from_station_id: Optional[int] = Field(None, description='源服务点ID')
    to_station_id: Optional[int] = Field(None, description='目标服务点ID')
    cart_id: int = Field(..., description='推车ID')
    priority: str = Field('normal', description='优先级: normal/urgent')
    quantity: int = Field(1, description='数量')
    reason: Optional[str] = Field(None, description='调拨原因')


class CrossVenueTransferApprovalIn(BaseModel):
    approval_status: str = Field(..., description='审批状态: approved/rejected')
    approver_comment: Optional[str] = Field(None, description='审批意见')


class CrossVenueTransportStartIn(BaseModel):
    transporter: Optional[str] = Field(None, description='运输方/司机')
    transport_tracking_no: Optional[str] = Field(None, description='运输跟踪号')


class CrossVenueTransportArriveIn(BaseModel):
    pass


class CrossVenueTransferOut(BaseModel):
    id: int
    transfer_no: str
    from_venue_id: int
    from_venue_name: str
    to_venue_id: int
    to_venue_name: str
    from_station_id: Optional[int] = None
    from_station_name: Optional[str] = None
    to_station_id: Optional[int] = None
    to_station_name: Optional[str] = None
    cart_id: int
    cart_no: str
    cart_type: str
    priority: str
    priority_display: str
    quantity: int
    reason: Optional[str] = None
    approval_status: str
    approval_status_display: str
    transport_status: str
    transport_status_display: str
    applicant_id: Optional[int] = None
    applicant_name: Optional[str] = None
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approver_comment: Optional[str] = None
    approval_at: Optional[datetime] = None
    transporter: Optional[str] = None
    transport_tracking_no: Optional[str] = None
    shipped_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    confirmer_id: Optional[int] = None
    confirmer_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
