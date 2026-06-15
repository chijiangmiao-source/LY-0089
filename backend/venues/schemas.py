from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class VenueIn(BaseModel):
    name: str
    venue_type: str = 'mall'
    address: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    total_floors: int = 5
    description: Optional[str] = None
    is_active: bool = True


class VenueOut(BaseModel):
    id: int
    name: str
    venue_type: str
    venue_type_display: str
    address: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    total_floors: int
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
