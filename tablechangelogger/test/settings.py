TABLE_CHANGE_LOG_CONFIG = {
    'TABLE_CHANGE_LOG_ENABLED': True,
    'LOGGABLE_APPS': {
        'mocks': {
            'tablechangelogger.seed.factories.MockClass': {
                'fields': ['route_id', 'pickup_point']
            }
        },
    }
}
SECRET_KEY = 'dummy'
INSTALLED_APPS = ('tablechangelogger', )
