from django.contrib.gis.db import models


class TableChangesLog(models.Model):
    app_label = models.CharField(max_length=255)
    table_name = models.CharField(max_length=255)
    instance_id = models.IntegerField()
    field_name = models.CharField(max_length=255)
    field_value = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        index_together = (('table_name', 'instance_id'))

    def __str__(self):
        return '{}_{}'.format(self.app_label, self.table_name)
