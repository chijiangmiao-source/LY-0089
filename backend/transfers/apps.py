from django.apps import AppConfig


class TransferConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transfers'
    verbose_name = '跨点调拨'
