import logging
from django.conf import settings

logger = logging.getLogger(__name__)

TABLE_CHANGE_LOG_CONFIG = getattr(settings, 'TABLE_CHANGE_LOG_CONFIG')
LOGGABLE_APPS = TABLE_CHANGE_LOG_CONFIG.get('LOGGABLE_APPS')

if not LOGGABLE_APPS:
    logger.exception('You should define LOGGABLE_APPS key inside your config!')
    TABLE_CHANGE_LOG_ENABLED = False
else:
    TABLE_CHANGE_LOG_ENABLED = TABLE_CHANGE_LOG_CONFIG.get(
        'TABLE_CHANGE_LOG_ENABLED', True)

LOGGABLE_MODELS = []

if TABLE_CHANGE_LOG_ENABLED:
    for _, table_config in LOGGABLE_APPS.items():
        LOGGABLE_MODELS.append(table_config)
