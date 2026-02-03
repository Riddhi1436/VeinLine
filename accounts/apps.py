from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import accounts.signals  # noqa
        import django_py314_patch  # noqa - Fix for Django 5.1.6 + Python 3.14 Context.__copy__ bug