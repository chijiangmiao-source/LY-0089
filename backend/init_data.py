# -*- coding: utf-8 -*-
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from stations.models import ServiceStation
from carts.models import Cart

User = get_user_model()


def init_data():
    print('=== 开始初始化示例数据 ===')

    admin_username = 'admin'
    if not User.objects.filter(username=admin_username).exists():
        User.objects.create_superuser(
            username=admin_username,
            email='admin@example.com',
            password='admin123456',
            full_name='系统管理员',
            role='admin',
        )
        print(f'✓ 创建管理员: {admin_username} / admin123456')

    staff_username = 'staff'
    if not User.objects.filter(username=staff_username).exists():
        User.objects.create_user(
            username=staff_username,
            password='staff123456',
            full_name='工作人员小王',
            role='staff',
        )
        print(f'✓ 创建工作人员: {staff_username} / staff123456')

    floors_data = [
        {'name': '1F 东门服务点', 'floor': 1, 'location': '东门入口左侧', 'safety_stock': 5},
        {'name': '1F 西门服务点', 'floor': 1, 'location': '西门入口右侧', 'safety_stock': 5},
        {'name': '2F 北区服务点', 'floor': 2, 'location': '2楼北区扶梯旁', 'safety_stock': 4},
        {'name': '2F 南区服务点', 'floor': 2, 'location': '2楼南区中庭', 'safety_stock': 4},
        {'name': '3F 儿童区服务点', 'floor': 3, 'location': '3楼儿童乐园门口', 'safety_stock': 8},
        {'name': 'B1 超市服务点', 'floor': -1, 'location': 'B1超市出口', 'safety_stock': 6},
    ]

    stations = []
    for data in floors_data:
        station, created = ServiceStation.objects.get_or_create(
            name=data['name'],
            defaults=data,
        )
        if created:
            print(f'✓ 创建服务点: {station.name}')
        stations.append(station)

    cart_counter = 1
    cart_types = ['standard', 'standard', 'standard', 'large']
    for station in stations:
        cart_count = station.safety_stock + 1
        for i in range(cart_count):
            cart_no = f'ST{station.floor:02d}{cart_counter:04d}'
            cart, created = Cart.objects.get_or_create(
                cart_no=cart_no,
                defaults={
                    'station': station,
                    'cart_type': cart_types[i % len(cart_types)],
                    'status': 'available',
                },
            )
            if created:
                print(f'✓ 创建推车: {cart_no} @ {station.name}')
            cart_counter += 1

    print('=== 初始化完成 ===')


if __name__ == '__main__':
    init_data()
