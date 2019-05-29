from django.contrib.gis.db import models

from tablechangelogger.config import TABLE_CHANGE_LOG_ENABLED
from tablechangelogger.fields import LoggedField

if TABLE_CHANGE_LOG_ENABLED:
    from tablechangelogger.signals import *  # noqa


class TableChangesLog(models.Model):
    app_label = models.CharField(max_length=255)
    table_name = models.CharField(max_length=255)
    instance_id = models.IntegerField()
    field_name = models.CharField(max_length=255)
    log = LoggedField(max_length=10485000, null=True)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        index_together = (('table_name', 'instance_id'))

    def __str__(self):
        return '{}_{}'.format(self.table_name, self.instance_id)
