import factory
from faker import Factory

from tablechangelogger.models import TableChangesLog

faker = Factory.create()


class TableChangesLogFactory(factory.DjangoModelFactory):
    class Meta:
        model = TableChangesLog
        django_get_or_create = ('instance_id', )
