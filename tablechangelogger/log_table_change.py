import logging

from tablechangelogger.config import LOGGABLE_APPS
from tablechangelogger.utils import get_app_label, get_model, get_model_name
from tablechangelogger.datastructures import Logged

logger = logging.getLogger(__name__)


def is_loggable(instance):
    """
        Determines whether the instance model or app label is loggable
        to TableChangeLog
    """
    is_loggable = False
    app_label = get_app_label(instance)
    table_name = get_model_name(instance)
    config = LOGGABLE_APPS.get(app_label)

    if config is not None:
        for model_path in config.keys():
            is_loggable = table_name in model_path
            if is_loggable:
                break

    return is_loggable


def get_differing_fields(first_instance, second_instance):
    """Returns differing field names of two instances of the same type"""

    differing_fields = []

    if all([first_instance is None, second_instance is None]):
        return differing_fields

    if any([first_instance is None, second_instance is None]):
        nonempty_instance = (first_instance if first_instance is not None else
                             second_instance)
        field_names = nonempty_instance._meta.get_fields()
        field_names = list(map(lambda field: field.name, field_names))
        return field_names

    # get common field names
    field_names = first_instance._meta.get_fields()
    field_names = list(map(lambda field: field.name, field_names))

    differing_fields = list(filter(
         lambda field_name: getattr(first_instance, field_name, None) !=
         getattr(second_instance, field_name, None), field_names
    ))

    return differing_fields


def get_loggable_fields(differing_fields, config):
    """
    Get table change loggable fields from differing field names list for a
    specific model

    Arguments:
        differing_fields: (list) List of differing field names: ['driver_id', ]
        config: table change log config mapping for specific table name
    """

    fields = config.get('fields')
    loggable_fields = list(filter(lambda field_name: field_name in fields,
                                  differing_fields))

    return loggable_fields


def get_table_change_log_config(instance):
    """Returns table change log config based on instance"""

    app_label = get_app_label(instance)
    table_name = get_model_name(instance)
    config = LOGGABLE_APPS.get(app_label)
    table_path = list(filter(lambda key: table_name in key, config.keys()))

    if table_path:
        table_path = table_path[0]

    table_config = config.get(table_path)

    return table_config


def create_table_change_log_record(app_label, table_name, instance_id,
                                   field_name, log):
    """
        Creates TableChangeLog record and returns the created instance
    """
    from tablechangelogger.models import TableChangesLog

    table_change_log = TableChangesLog.objects.create(
        app_label=app_label, table_name=table_name,
        instance_id=instance_id, field_name=field_name,
        log=log
    )
    return table_change_log


def get_latest_table_change_log(table_name, instance_id):
    """
        Returns most recent TableChangeLog record from specified table and
        instance
    """

    from tablechangelogger.models import TableChangesLog

    return TableChangesLog.objects.filter(
        table_name=table_name, instance_id=instance_id
    ).order_by('created_at').last()


def log_table_change(func):
    def wrapper(sender, instance, *args, **kwargs):
        model = get_model(instance)

        try:
            obj = model.objects.get(id=instance.id)
        except Exception:
            obj = None

        try:
            result = func(sender, instance, *args, **kwargs)
            # get the instance from the pre_save method
            # check if the instance is loggable
            loggable = is_loggable(instance)
            if loggable:
                app_label = get_app_label(instance)
                table_name = get_model_name(instance)
                instance_id = instance.id
                # get differing fields
                differing_fields = get_differing_fields(obj, instance)
                # get respective config
                config = get_table_change_log_config(instance)
                loggable_fields = get_loggable_fields(differing_fields,
                                                      config)

                # for each loggable field, get its value and save to the
                # respective table
                for field_name in loggable_fields:
                    old_value = getattr(obj, field_name, None)
                    new_value = getattr(instance, field_name, None)
                    log = Logged(old_value=old_value, new_value=new_value)
                    create_table_change_log_record(
                        app_label,
                        table_name,
                        instance_id,
                        field_name,
                        log
                    )
                return result
        except Exception as e:
            logger.exception(e)
    return wrapper
