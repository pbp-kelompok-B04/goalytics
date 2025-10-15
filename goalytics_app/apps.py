from django.apps import AppConfig


class GoalyticsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'goalytics_app'

    def ready(self):
        from . import signals