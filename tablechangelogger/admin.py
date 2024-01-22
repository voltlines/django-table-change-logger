import json

from django.apps import apps
from django.contrib import admin
from django.utils.html import format_html

from tablechangelogger.models import TableChangesLog
from tablechangelogger.log_table_change import (
    get_notifiable_table_change_fields, get_old_changes)


class TableChangesLogAdmin(admin.ModelAdmin):
    exclude = ('log', )
    list_display = ('id', 'get_related_obj', 'table_name', 'field_name',
                    'get_previous_log_link', 'get_old', 'get_new',
                    'get_notifiable_fields', 'is_notified', 'details',
                    'created_at')
    list_filter = ('app_label', 'table_name', 'is_notified', )
    search_fields = ('instance_id', 'table_name', 'field_name', 'app_label')
    ordering = ('-created_at', )

    def get_previous_log_link(self, obj):
        if obj.previous_log:
            return format_html(
                '<a href="/admin/tablechangelogger/tablechangeslog/'
                '{0}/change/">Log</a>', obj.previous_log.id)

    def get_notifiable_fields(self, obj):
        notifiable_fields = get_notifiable_table_change_fields(obj)
        if not notifiable_fields:
            return format_html(
                '<div style="width: 100%; height: 100%; background-color: '
                '{0}; border-radius: 5px">'
                '<p style="color: {1}">Won"t Notify</p></div>', 'red', 'white'
            )
        return ', '.join(notifiable_fields)

    def get_old(self, obj):
        kwargs = {
            'property_unique_ids': obj.property_unique_ids,
            'field_names': obj.field_name,
            'table_name': obj.table_name,
            'app_label': obj.app_label,
            'instance_id': obj.instance_id,
            'log': obj.log
        }
        changes_dict = get_old_changes(**kwargs)
        return changes_dict

    def get_new(self, obj):
        try:
            return json.dumps(obj.log.get_new_values())
        except Exception:
            return ''

    def get_related_obj(self, obj):
        Model = apps.get_model(obj.app_label, obj.table_name)
        instance = Model.objects.get(pk=obj.instance_id)
        return (
            '<a href="/admin/%s/%s/%s/change/">%s</a>' % (
                obj.app_label, obj.table_name.lower(), obj.instance_id,
                instance.__str__()
            ))

    def get_readonly_fields(self, request, obj=None):
        return [f for f in self.list_display]

    get_previous_log_link.allow_tags = True
    get_previous_log_link.short_description = 'Previous Log Link'
    get_old.short_description = 'Old Values'
    get_new.short_description = 'New Values'
    get_notifiable_fields.short_description = 'Notifiable Fields'
    get_notifiable_fields.allow_tags = True
    get_related_obj.allow_tags = True
    get_related_obj.short_description = 'Related Object'


admin.site.register(TableChangesLog, TableChangesLogAdmin)
