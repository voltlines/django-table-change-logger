from django.apps import apps
from django.contrib import admin

from tablechangelogger.models import TableChangesLog
from tablechangelogger.log_table_change import (
    get_notifiable_table_change_fields)


class TableChangesLogAdmin(admin.ModelAdmin):

    exclude = ('log', )
    list_display = ('id', 'table_name', 'field_name',
                    'unique_id', 'get_previous_log_link', 'get_changes',
                    'get_notifiable_fields', 'is_notified', 'details',
                    'get_related_obj')
    list_filter = ('app_label', 'table_name', )
    search_fields = ('instance_id', 'table_name', 'field_name', 'app_label')

    def get_previous_log_link(self, obj):
        if obj.previous_log:
            return (
                '<a href="/admin/tablechangelogger/tablechangeslog/'
                '%s/change/">Log</a>' % (obj.previous_log.id))

    def get_notifiable_fields(self, obj):
        notifiable_fields = get_notifiable_table_change_fields(obj)
        return ', '.join(notifiable_fields)

    def get_changes(self, obj):
        changes = obj.log.changes
        changes_dict = {change_key: change_obj.new_value
                        for change_key, change_obj in changes.items()}
        return changes_dict

    def get_related_obj(self, obj):
        Model = apps.get_model(obj.app_label, obj.table_name)
        instance = Model.objects.get(id=obj.instance_id)
        return (
            '<a href="/admin/%s/%s/%s/change/">%s</a>' % (
                obj.app_label, obj.table_name.lower(), obj.instance_id,
                instance.__str__()
            ))

    def get_readonly_fields(self, request, obj=None):
        return [f for f in self.list_display]

    get_previous_log_link.allow_tags = True
    get_previous_log_link.short_description = 'Previous Log Link'
    get_changes.short_description = 'Changes'
    get_notifiable_fields.short_description = 'Notifiable Fields'
    get_related_obj.allow_tags = True
    get_related_obj.short_description = 'Related Object'


admin.site.register(TableChangesLog, TableChangesLogAdmin)
