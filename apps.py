from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ExpensesAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'expenses'
    label = 'expenses'
    verbose_name = _('Expenses')

    def ready(self):
        pass
