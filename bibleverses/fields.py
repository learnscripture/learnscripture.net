from django.db import models
from south.modelsinspector import add_introspection_rules

add_introspection_rules([], ["^bibleverses\.fields\.VectorField"])


class VectorField(models.Field):

    def __init__(self, *args, **kwargs):
        kwargs['null'] = True
        kwargs['editable'] = False
        kwargs['serialize'] = False
        super(VectorField, self).__init__(*args, **kwargs)

    def db_type(self, connection, **kwargs):
        return 'tsvector'
