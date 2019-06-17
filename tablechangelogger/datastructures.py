class Change(object):
    def __init__(self, new_value, old_value):
        self.new_value = new_value
        self.old_value = old_value

    def __str__(self):
        return '{} --> {}'.format(self.new_value, self.old_value)


class Logged(object):
    def __init__(self, changes, created=False):
        self.changes = changes
        self.created = created

    def __str__(self):
        keys = self.changes.keys()
        values = self.changes.values()
        return '{} -> {}'.format(', '.join(keys), ', '.join(values))

    def get_field_log(self, field_name):
        return self.changes.get(field_name)

    def get_field_new_value(self, field_name):
        field_log = self.changes.get(field_name, {})
        return field_log.new_value if field_log else None

    def get_field_old_value(self, field_name):
        field_log = self.changes.get(field_name, {})
        return field_log.old_value if field_log else None
