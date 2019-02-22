import logging

from tablechangelogger.config import TABLE_CHANGE_LOG_CONFIG
from tablechangelogger.utils import get_app_label, get_model_name

logger = logging.getLogger(__name__)


def is_loggable(instance):
    """
        Determines whether the instance model or app label is loggable
        to TableChangeLog
    """
    is_loggable = False
    app_label = get_app_label(instance)
    table_name = get_model_name(instance)
    config = TABLE_CHANGE_LOG_CONFIG.get(app_label)

    if config is not None:
        for model_path in config.keys():
            is_loggable = table_name in model_path
            if is_loggable:
                break

    return is_loggable


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
    config = TABLE_CHANGE_LOG_CONFIG.get(app_label)
    table_config = config.get(table_name)

    return table_config


def create_table_change_log_record(app_label, table_name, instance_id,
                                   field_name, field_value):
    """
        Creates TableChangeLog record and returns the created instance
    """
    from tablechangelogger.models import TableChangesLog

    table_change_log = TableChangesLog.objects.create(
        app_label=app_label, table_name=table_name,
        instance_id=instance_id, field_name=field_name,
        field_value=field_value
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


def log_table_change(fields):
    def decorator(func):
        def wrapper(sender, instance, *args, **kwargs):
            try:
                result = func(sender, instance, *args, **kwargs)
                # get the instance from the pre_save method
                # check if the instance is loggable
                loggable = is_loggable(instance)

                if loggable:
                    app_label = get_app_label(instance)
                    table_name = get_model_name(instance)
                    instance_id = instance.id
                    # for each loggable field, get its value and save to the
                    # respective table
                    for field_name in fields:
                        field_value = getattr(instance, field_name, None)
                        if field_value:
                            create_table_change_log_record(
                                app_label,
                                table_name,
                                instance_id,
                                field_name,
                                field_value
                            )
                    return result
            except Exception as e:
                logger.exception(e)
        return wrapper
    return decorator
