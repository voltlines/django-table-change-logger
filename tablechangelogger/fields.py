from django.db import models

from tablechangelogger.utils import serialize_field, deserialize_field
from tablechangelogger.datastructures import Logged


def parse_log(value):
    svalue = value.split('~')
    old, new = svalue[0], svalue[1]
    old_obj, new_obj = deserialize_field(old), deserialize_field(new)
    return Logged(old_value=old_obj, new_value=new_obj)


class LoggedField(models.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        return super().deconstruct()

    def pre_save(self, model_instance, add):
        log = model_instance.log
        new_field = log.new_value
        old_field = log.old_value
        snew = serialize_field(new_field)
        sold = serialize_field(old_field)
        value = '{}~{}'.format(sold, snew)
        return value

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return parse_log(value)

    def get_prep_value(self, value):
        if not value or isinstance(value, str):
            return value
        return '{}~{}'.format(serialize_field(value.old_value),
                              serialize_field(value.new_value))

