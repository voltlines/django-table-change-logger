from django.db import models

from tablechangelogger.utils import serialize_field, deserialize_field
from tablechangelogger.datastructures import Logged


def parse_log(value):
    changes, created = value.split('~')
    changes = deserialize_field(changes)
    created = True if created == 'True' else False
    return Logged(changes=changes, created=created)


class LoggedField(models.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        return super().deconstruct()

    def pre_save(self, model_instance, add):
        log = model_instance.log
        changes = log.changes
        created = log.created
        value = '{}~{}'.format(serialize_field(changes), created)
        return value

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return parse_log(value)

    def get_prep_value(self, value):
        if not value or isinstance(value, str):
            return value
        return '{}~{}'.format(serialize_field(value.changes),
                              value.created)
