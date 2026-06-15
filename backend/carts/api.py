from datetime import datetime
from django.shortcuts import get_object_or_404
from ninja import Router, Query
from ninja.pagination import paginate

from .models import Cart
from .schemas import CartIn, CartOut


router = Router()


def cart_to_out(cart: Cart) -> CartOut:
    return CartOut(
        id=cart.id,
        cart_no=cart.cart_no,
        station_id=cart.station_id,
        station_name=cart.station.name if cart.station else '',
        cart_type=cart.cart_type,
        status=cart.status,
        status_display=cart.status_display,
        last_clean_time=cart.last_clean_time,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


@router.get('/', response=list[CartOut])
@paginate
def list_carts(request):
    queryset = Cart.objects.select_related('station').all()
    return [cart_to_out(cart) for cart in queryset]


@router.get('/{cart_id}', response=CartOut)
def get_cart(request, cart_id: int):
    cart = get_object_or_404(Cart.objects.select_related('station'), id=cart_id)
    return cart_to_out(cart)


@router.post('/', response=CartOut)
def create_cart(request, payload: CartIn):
    cart = Cart.objects.create(
        cart_no=payload.cart_no,
        station_id=payload.station_id,
        cart_type=payload.cart_type,
        status=payload.status,
        last_clean_time=payload.last_clean_time,
    )
    cart.refresh_from_db()
    cart = Cart.objects.select_related('station').get(id=cart.id)
    return cart_to_out(cart)


@router.put('/{cart_id}', response=CartOut)
def update_cart(request, cart_id: int, payload: CartIn):
    cart = get_object_or_404(Cart, id=cart_id)
    cart.cart_no = payload.cart_no
    cart.station_id = payload.station_id
    cart.cart_type = payload.cart_type
    cart.status = payload.status
    cart.last_clean_time = payload.last_clean_time
    cart.save()
    cart = Cart.objects.select_related('station').get(id=cart.id)
    return cart_to_out(cart)


@router.delete('/{cart_id}')
def delete_cart(request, cart_id: int):
    cart = get_object_or_404(Cart, id=cart_id)
    cart.delete()
    return {'success': True}


@router.post('/{cart_id}/clean', response=CartOut)
def clean_cart(request, cart_id: int):
    cart = get_object_or_404(Cart.objects.select_related('station'), id=cart_id)
    cart.last_clean_time = datetime.now()
    cart.status = 'available'
    cart.save()
    return cart_to_out(cart)
