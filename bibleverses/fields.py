from django.db import models


class VectorField(models.Field):

    def __init__(self, *args, **kwargs):
        kwargs['null'] = True
        kwargs['editable'] = False
        kwargs['serialize'] = False
        super(VectorField, self).__init__(*args, **kwargs)

    def db_type(self, connection, **kwargs):
        return 'tsvector'

    def deconstruct(self):
        name, path, args, kwargs = super(VectorField, self).deconstruct()
        for a in ['null', 'editable', 'serialize']:
            try:
                del kwargs[a]
            except KeyError:
                pass
        return name, path, args, kwargs
