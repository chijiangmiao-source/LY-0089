# -*- coding: utf-8 -*-
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rentals.models import RentalRecord


def fix_returned_overdue():
    """
    修复已归还但状态仍为 overdue 的记录：
    - 有 return_time 的记录如果 stage='overdue'，改为 stage='returned' 并标记 is_overdue=True
    - 没有 return_time 但超过期限的 borrowing 记录，如未还则保持，已还需按上面处理
    """
    print('=== 修复归还记录状态 ===')

    fixed_count = 0

    records = RentalRecord.objects.filter(return_time__isnull=False)
    for rec in records:
        changed = False
        if rec.stage == 'overdue':
            rec.stage = 'returned'
            changed = True
        if not rec.is_overdue:
            from django.conf import settings
            from datetime import timedelta
            duration = rec.return_time - rec.borrow_time
            if duration > timedelta(hours=settings.RENTAL_OVERDUE_HOURS):
                rec.is_overdue = True
                changed = True
        if changed:
            rec.save()
            fixed_count += 1
            print(f'✓ 修复记录: {rec.rental_no}  stage={rec.stage}  is_overdue={rec.is_overdue}')

    print(f'=== 完成，共修复 {fixed_count} 条记录 ===')


if __name__ == '__main__':
    fix_returned_overdue()
