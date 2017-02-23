from django.apps import AppConfig


class UserConfig(AppConfig):  # Our app config class
    name = 'user'
    verbose_name = "User"

    def ready(self):
        import user.signals