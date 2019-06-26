from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from django.utils.module_loading import import_string

from tablechangelogger.config import TABLE_CHANGE_LOG_ENABLED
from tablechangelogger.fields import LoggedField
from tablechangelogger.log_table_change import (
    get_notifiable_table_change_fields,
    get_table_change_log_config
)

if TABLE_CHANGE_LOG_ENABLED:
    from tablechangelogger.signals import *  # noqa


class TableChangesLog(models.Model):
    app_label = models.CharField(max_length=255)
    table_name = models.CharField(max_length=255)
    instance_id = models.IntegerField()
    field_name = models.CharField(max_length=255)
    log = LoggedField(max_length=10485000, null=True)
    created_at = models.DateTimeField(auto_now=True)
    unique_id = models.CharField(max_length=300, blank=True, null=True)
    property_unique_ids = JSONField(default=dict, null=True, blank=True)
    is_notified = models.BooleanField(default=False)
    details = JSONField(default=dict, null=True, blank=True)

    class Meta:
        index_together = (('table_name', 'instance_id'))

    def __str__(self):
        return '{}_{}'.format(self.table_name, self.instance_id)

    @property
    def previous_log(self):
        return self._meta.model.objects.order_by('created_at').filter(
            instance_id=self.instance_id,
            table_name=self.table_name,
            app_label=self.app_label,
            created_at__lte=self.created_at
        ).exclude(id=self.id).last()


@receiver(post_save, sender=TableChangesLog)
def tcl_post_save_actions(instance, created, **kwargs):
    if not instance.log.created:
        Model = apps.get_model(instance.app_label, instance.table_name)
        logged_instance = Model.objects.get(id=instance.instance_id)
        config = get_table_change_log_config(logged_instance)

        function_path = config.get('callback', '')
        try:
            func = import_string(function_path)
        except ImportError:
            return

        notifiable_fields = get_notifiable_table_change_fields(instance)
        new_values = instance.log.get_new_values()

        # remove fields which became null
        for field in notifiable_fields:
            change_value = new_values[field]
            if change_value is None:
                notifiable_fields.remove(field)

        if notifiable_fields:
            func(instance, notifiable_fields)
