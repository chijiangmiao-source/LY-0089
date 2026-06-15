# -*- coding: utf-8 -*-
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


def create_default_users():
    print('=== 创建默认用户 ===')

    users_data = [
        {
            'username': 'admin',
            'password': 'admin123456',
            'email': 'admin@example.com',
            'full_name': '系统管理员',
            'role': 'admin',
            'is_superuser': True,
            'is_staff': True,
        },
        {
            'username': 'staff',
            'password': 'staff123456',
            'email': 'staff@example.com',
            'full_name': '工作人员小王',
            'role': 'staff',
            'is_superuser': False,
            'is_staff': False,
        },
    ]

    for data in users_data:
        username = data['username']
        if User.objects.filter(username=username).exists():
            print(f'⚠  用户已存在，跳过: {username}')
            continue

        is_super = data.pop('is_superuser')
        is_staff_flag = data.pop('is_staff')
        password = data.pop('password')

        if is_super:
            user = User.objects.create_superuser(
                username=username,
                password=password,
                **data,
            )
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                is_staff=is_staff_flag,
                **data,
            )
        print(f'✓ 创建用户成功: {username} / {password}（{user.full_name}）')

    print('=== 完成 ===')


if __name__ == '__main__':
    create_default_users()
