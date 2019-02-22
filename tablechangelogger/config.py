from django.conf import settings

TABLE_CHANGE_LOG_CONFIG = getattr(settings, 'TABLE_CHANGE_LOG_CONFIG')

LOGGABLE_APP_LABELS = list(TABLE_CHANGE_LOG_CONFIG.keys())
LOGGABLE_MODELS = []

for _, table_config in TABLE_CHANGE_LOG_CONFIG.items():
    LOGGABLE_MODELS.append(table_config)
