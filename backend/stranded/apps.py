from django.apps import AppConfig


class StrandedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stranded'
    verbose_name = '滞留上报'
