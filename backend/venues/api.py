from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import paginate

from .models import Venue
from .schemas import VenueIn, VenueOut


router = Router()


def venue_to_out(venue: Venue) -> VenueOut:
    return VenueOut(
        id=venue.id,
        name=venue.name,
        venue_type=venue.venue_type,
        venue_type_display=venue.venue_type_display,
        address=venue.address,
        contact_person=venue.contact_person,
        contact_phone=venue.contact_phone,
        total_floors=venue.total_floors,
        description=venue.description,
        is_active=venue.is_active,
        created_at=venue.created_at,
        updated_at=venue.updated_at,
    )


@router.get('/', response=list[VenueOut])
@paginate
def list_venues(request, is_active: bool = None):
    queryset = Venue.objects.all()
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    return [venue_to_out(v) for v in queryset]


@router.get('/all', response=list[VenueOut])
def list_all_venues(request, is_active: bool = None):
    queryset = Venue.objects.all()
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    return [venue_to_out(v) for v in queryset.order_by('name')]


@router.get('/{venue_id}', response=VenueOut)
def get_venue(request, venue_id: int):
    venue = get_object_or_404(Venue, id=venue_id)
    return venue_to_out(venue)


@router.post('/', response=VenueOut)
def create_venue(request, payload: VenueIn):
    venue = Venue.objects.create(**payload.dict())
    return venue_to_out(venue)


@router.put('/{venue_id}', response=VenueOut)
def update_venue(request, venue_id: int, payload: VenueIn):
    venue = get_object_or_404(Venue, id=venue_id)
    for k, v in payload.dict().items():
        setattr(venue, k, v)
    venue.save()
    return venue_to_out(venue)


@router.delete('/{venue_id}')
def delete_venue(request, venue_id: int):
    venue = get_object_or_404(Venue, id=venue_id)
    venue.delete()
    return {'success': True}
