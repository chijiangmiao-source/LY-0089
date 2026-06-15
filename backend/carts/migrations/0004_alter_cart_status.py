from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0003_alter_cart_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='status',
            field=models.CharField(
                choices=[
                    ('available', '可用'),
                    ('reserved', '已预约'),
                    ('borrowed', '借出中'),
                    ('stranded', '滞留'),
                    ('transferring', '调拨中'),
                    ('cleaning', '清洁中'),
                    ('reset_check', '复位检查中'),
                    ('maintenance', '维修中'),
                    ('scrapped', '已报废'),
                ],
                default='available',
                max_length=20,
                verbose_name='当前状态'
            ),
        ),
    ]
