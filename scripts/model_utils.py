from datetime import date

import visidata
from django.db.models import QuerySet


def get_main_attrs(instance):
    if hasattr(instance, '_meta'):
        return meta_to_col_list(instance._meta)
    elif hasattr(instance, '__attrs_attrs__'):
        return [(field.name, field.type or visidata.anytype)
                for field in instance.__attrs_attrs__]
    return []


def meta_to_col_list(_meta):
    retval = []
    for field in _meta.get_fields():
        if not hasattr(field, 'get_attname'):
            continue
        if getattr(field, 'many_to_many', False):
            continue
        retval.append((field.get_attname(), django_to_vd_type(field)))
    return retval


def django_to_vd_type(field):
    return {
        'AutoField': int,
        'BigAutoField': int,
        'BigIntegerField': int,
        'BooleanField': int,
        'DateField': date,
        'DecimalField': float,
        'FloatField': float,
        'ForeignKey': int,  # good enough for now...
        'PositiveIntegerField': int,
        'PositiveSmallIntegerField': int,
        'SmallIntegerField': int,
        'CharField': str,
        'TextField': str,
    }.get(field.get_internal_type(), visidata.anytype)


class QuerySetSheet(visidata.Sheet):
    rowtype = 'rows'  # rowdef: model instance

    @visidata.asyncthread
    def reload(self):
        self.rows = []
        self.columns = []
        for name, t in meta_to_col_list(self.source.model._meta):
            self.addColumn(visidata.ColumnAttr(name, type=t))
        for item in visidata.Progress(self.source.iterator(), total=self.source.count()):
            self.addRow(item)


class AutoSheet(visidata.TableSheet):
    rowtype = 'rows'  # rowdef: attrs instance

    @visidata.asyncthread
    def reload(self):
        self.columns = []
        if len(self.source) == 0:
            return
        for name, t in get_main_attrs(self.source[0]):
            self.addColumn(visidata.ColumnAttr(name, type=t))
        for row in self.source:
            self.addRow(row)


def vd(objects):
    """
    Wrapper around visidata.run with custom sheet types
    """
    sheet = None
    if isinstance(objects, QuerySet):
        sheet = QuerySetSheet(objects.model.__name__, source=objects)
    elif isinstance(objects, list) and len(objects) > 0:
        instance = objects[0]
        if hasattr(instance, '_meta') or hasattr(instance, '__attrs_attrs__'):
            sheet = AutoSheet(instance.__class__.__name__, source=objects)
    if sheet is None:
        sheet = visidata.load_pyobj('', objects)

    return visidata.run(sheet)
