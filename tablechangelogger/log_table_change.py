from datetime import datetime
import logging
from hashlib import md5

from django.db import IntegrityError
from django.db.models import Q
from django.db.models.base import Model
from tablechangelogger.config import LOGGABLE_APPS
from tablechangelogger.utils import (
    get_app_label, get_model, get_model_name, serialize_field,
    is_same_dictionary)
from tablechangelogger.datastructures import Logged, Change

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
            # if instance is newly created, we cannot log it since
            # there is no change
            is_loggable &= instance.id is not None
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


def generate_changes_string(new_values):
    changes = ''
    for key, value in new_values.items():
        if isinstance(value, Model):
            changes += '{}:{}'.format(value._meta, hash(value))
        else:
            changes += '{}:{}'.format(key, value)
    return changes


def generate_tcl_unique_id(app_label, table_name, instance_id, field_names,
                           new_values):
    """
    Generates a unique id from specific log attributes.
    """

    changes = generate_changes_string(new_values)
    key = '{}{}{}{}{}'.format(app_label, table_name, instance_id, field_names,
                              changes)

    return md5(str(key).encode()).hexdigest()


def generate_tcl_property_unique_ids_dict(loggable_properties, changes):
    """
    Gets a loggable propertes list and changes mapping,
    generates a mapping of property fields and values and generates a hash
    for each of these properties.
    """

    unique_id_dict = {}
    prop_changes = {prop: serialize_field(value.new_value)
                    for prop, value in changes.items()
                    if prop in loggable_properties}
    for key, value in prop_changes.items():
        unique_id_dict[key] = md5(str(value).encode()).hexdigest()

    return unique_id_dict


def create_table_change_log_record(app_label, table_name, instance_id,
                                   field_names, log, loggable_properties=None):
    """
    Creates TableChangeLog record and returns the created instance
    """
    from tablechangelogger.models import TableChangesLog

    unique_id = generate_tcl_unique_id(
        app_label, table_name, instance_id, field_names,
        log.get_new_values())
    property_unique_ids_dict = generate_tcl_property_unique_ids_dict(
        loggable_properties, log.changes)

    is_unique_log = True
    tcl_exists = TableChangesLog.objects.filter(unique_id=unique_id).exists()
    old_changes = get_old_changes(
        property_unique_ids=property_unique_ids_dict,
        field_names=field_names,
        table_name=table_name,
        app_label=app_label,
        instance_id=instance_id,
        log=log)
    new_changes = log.get_new_values()

    is_same_log = is_same_dictionary(old_changes, new_changes)
    is_unique_log = not tcl_exists and not is_same_log

    if is_unique_log:
        try:
            TableChangesLog.objects.create(
                app_label=app_label, table_name=table_name,
                instance_id=instance_id, field_name=field_names,
                log=log, unique_id=unique_id,
                property_unique_ids=property_unique_ids_dict
            )
        except IntegrityError as e:
            logger.exception(e)


def create_log_object(loggable_fields, instance, old_instance=None):
    """
    Create TableChangesLog log attribute.

    Args:
        loggable_fields: <list> A list of loggable fields
        new_instance: <Model instance> A newly saved Django model instance
        old_instance: <Model instance|optional> Old version of the instance
        argument
    """

    # initialize variables
    changes = {}
    log = None

    # for each loggable field, get its value and save to the
    # respective table
    for field_name in loggable_fields:
        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(instance, field_name, None)
        change = Change(old_value=old_value, new_value=new_value)
        changes[field_name] = change

    # if changes exist, create the log object
    if changes:
        created = old_instance is None
        log = Logged(changes=changes, created=created)

    return log


def create_initial_change_log_record(instance):
    """
    Creates a TableChangesLog record for a newly created instance.
    """

    app_label = get_app_label(instance)
    table_name = get_model_name(instance)
    config = get_table_change_log_config(instance)
    loggable_properties = get_loggable_properties(instance, config)
    field_names = ','.join(loggable_properties)
    log = create_log_object(loggable_properties, instance)
    create_table_change_log_record(
        app_label,
        table_name,
        instance.id,
        field_names,
        log,
        loggable_properties
    )


def get_latest_table_change_log(table_name, instance_id, field_name=None):
    """
        Returns most recent TableChangeLog record from specified table and
        instance
    """

    from tablechangelogger.models import TableChangesLog

    query = Q(table_name=table_name) & Q(instance_id=instance_id)

    if field_name:
        query &= Q(field_name__icontains=field_name)

    return TableChangesLog.objects.filter(query).order_by('created_at').last()


def get_notifiable_table_change_fields(tcl):
    """
    Returns notifiable property names and fields for TableChangesLog.

    Args:
        tcl: <TableChangesLog> A TableChangesLog object

    Returns:
        notifiable_fields: <set> A set of notifiable field names
    """

    field_names = tcl.field_name.split(',')
    notifiable_field_names = set()

    # base case: if tcl is a newly created one, there is no change in any
    # field, they are just initialized.
    if tcl.log.created:
        return notifiable_field_names

    previous_tcl = tcl.previous_log

    # Check if logged properties are changed
    # If so, add them to notifiable field names set
    for field in field_names:
        current_unique_id = tcl.property_unique_ids.get(field)

        if not current_unique_id:
            notifiable_field_names.add(field)
            continue
        # no field to check against, no change detected
        if not previous_tcl:
            continue

        previous_unique_id = previous_tcl.property_unique_ids.get(field)
        property_changed = current_unique_id != previous_unique_id

        if property_changed:
            notifiable_field_names.add(field)

    new_values = tcl.log.get_new_values()

    # remove fields which became null
    fields_to_remove = []
    for field in notifiable_field_names:
        change_value = new_values[field]
        if change_value is None:
            fields_to_remove.append(field)

    for field in fields_to_remove:
        notifiable_field_names.remove(field)

    return notifiable_field_names


def get_loggable_properties(instance, config):
    """
    Gets related instance config, inspects loggable fields,
    returns loggable properties among those fields.
    """

    fields = config.get('fields')
    model = instance._meta.model
    property_names = [
        name for name in dir(model)
        if isinstance(getattr(model, name), property)
    ]
    loggable_properties = list(
        filter(lambda prop: prop in fields, property_names))
    return loggable_properties


def get_old_changes(**kwargs):
    """
    Gets old instance changes of a TableChangesLog instance as a dictionary.

    Kwargs:
        property_unique_ids (dict)
        field_names (str)
        table_name (str)
        app_label(str)
        instance_id (int)
        log (Logged)
        pk (int, optional)
    """

    property_unique_ids = kwargs.get('property_unique_ids')
    field_names = kwargs.get('field_names')
    table_name = kwargs.get('table_name')
    app_label = kwargs.get('app_label')
    instance_id = kwargs.get('instance_id')
    log = kwargs.get('log')
    pk = kwargs.get('pk')

    properties = (list(property_unique_ids.keys())
                  if property_unique_ids else [])
    fields = field_names.split(',')
    loggable_fields = [field for field in set(fields)
                       if field not in properties]
    prev_log = get_previous_log(instance_id, table_name, app_label, pk=pk)

    changes_dict = {}

    if prev_log:
        prev_changes = prev_log.log.changes
        existing_property_changes = [prop for prop in properties
                                     if prop in prev_changes.keys()]
        changes_dict = {key: prev_changes.get(key).new_value
                        for key in existing_property_changes}

    current_changes = log.changes

    for field in loggable_fields:
        changes_dict[field] = current_changes.get(field).old_value

    return changes_dict


def get_previous_log(instance_id, table_name, app_label, pk=None):
    from tablechangelogger.models import TableChangesLog

    queryset = TableChangesLog.objects.order_by('created_at').filter(
        instance_id=instance_id,
        table_name=table_name,
        app_label=app_label,
        created_at__lte=datetime.now())
    if pk:
        queryset = queryset.exclude(id=pk)
    return queryset.last()


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
                # get differing fields
                differing_fields = get_differing_fields(obj, instance)
                # get respective config
                config = get_table_change_log_config(instance)
                # get properties to log
                loggable_properties = get_loggable_properties(
                    instance, config)
                # get fields to log
                loggable_fields = get_loggable_fields(differing_fields,
                                                      config)
                # merge properties and loggable fields
                loggable_fields = loggable_fields + loggable_properties

                # create log changes mapping
                log = create_log_object(loggable_fields, instance, obj)

                if log:
                    field_names = ','.join(loggable_fields)
                    create_table_change_log_record(
                        app_label,
                        table_name,
                        instance.id,
                        field_names,
                        log,
                        loggable_properties
                    )
                return result
        except Exception as e:
            logger.exception(e)
    return wrapper
