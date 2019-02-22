from django.apps import AppConfig


class TableChangeLoggerConfig(AppConfig):
    name = 'tablechangelogger'

    def ready(self):
        from tablechangelogger import signals  # noqa
