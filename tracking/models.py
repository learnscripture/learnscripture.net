from StringIO import StringIO
from httplib import HTTPResponse
import importlib

from django.core.handlers.wsgi import WSGIRequest
from django.db import models
from django.utils import timezone
from django.utils.functional import wraps
from json_field import JSONField


SNAPSHOT_INSERT = 'insert'
SNAPSHOT_UPDATE = 'update'
SNAPSHOT_DELETE = 'delete'

SNAPSHOT_TYPE_CHOICES = [
    (SNAPSHOT_INSERT, 'Insert'),
    (SNAPSHOT_UPDATE, 'Update'),
    (SNAPSHOT_DELETE, 'Delete'),
]


def get_fields(instance):
    if instance is None:
        return {}
    model = instance.__class__
    d = dict([(f.attname, getattr(instance, f.attname))
              for f in model._meta.fields])
    if 'id' not in d or d['id'] is None:
        raise ValueError("Can't save state of '%s' %s because 'id' is missing" % (instance, model))
    return d


def model_to_path(model):
    return "{0}.{1}".format(model.__module__, model.__name__)


class TrackingSnapshot(models.Model):
    model_path = models.CharField(max_length=255)
    created = models.DateTimeField(default=timezone.now)
    snapshot_type = models.CharField(max_length=20, choices=SNAPSHOT_TYPE_CHOICES)
    applied = models.BooleanField()
    old_fields = JSONField()
    new_fields = JSONField()

    class Meta:
        ordering = ['created']

    def __repr__(self):
        return "<TrackingSnapshot {0}(id={1}) {2} {3}{4}>".format(
            self.model_path,
            self.old_fields['id'] if self.snapshot_type == SNAPSHOT_DELETE else self.new_fields['id'],
            self.snapshot_type,
            self.created,
            " " + self.diff() if self.snapshot_type == SNAPSHOT_UPDATE else '')

    def diff(self):
        return '\n' + '\n'.join('{0}: {1} -> {2}'.format(key, self.old_fields[key], self.new_fields[key])
                                for key in self.old_fields.keys() if self.old_fields[key] != self.new_fields[key])

    @classmethod
    def register_insert(cls, instance):
        return cls._save_state(None, instance, SNAPSHOT_INSERT)

    @classmethod
    def register_update(cls, old_instance, new_instance):
        return cls._save_state(old_instance, new_instance, SNAPSHOT_UPDATE)

    @classmethod
    def register_delete(cls, instance):
        return cls._save_state(instance, None, SNAPSHOT_DELETE)

    @classmethod
    def _save_state(cls, old_instance, new_instance, snapshot_type):
        ref_instance = old_instance if old_instance is not None else new_instance
        model = ref_instance.__class__
        model_path = model_to_path(model)
        snapshot = cls.objects.create(model_path=model_path,
                                      old_fields=get_fields(old_instance),
                                      new_fields=get_fields(new_instance),
                                      snapshot_type=snapshot_type,
                                      applied=True,
                                      )
        return snapshot

    def apply(self):
        return self._do_apply(True)

    def unapply(self):
        return self._do_apply(False)

    def _do_apply(self, forward):
        if self.applied == forward:
            return

        backward = not forward
        snapshot_type = self.snapshot_type
        module_name, model_name = self.model_path.rsplit('.', 1)
        model = getattr(importlib.import_module(module_name), model_name)

        update_fields = self.new_fields if forward else self.old_fields
        delete_fields = self.old_fields if forward else self.new_fields

        if (forward and snapshot_type == SNAPSHOT_DELETE) or \
           (backward and snapshot_type == SNAPSHOT_INSERT):
            model.objects.filter(id=delete_fields['id']).delete()
        elif (forward and snapshot_type == SNAPSHOT_INSERT) or \
             (backward and snapshot_type == SNAPSHOT_DELETE):
            # Need to do raw insert that includes PK
            instance = model(**update_fields)
            instance.save_base(raw=True, force_insert=True)
        else:
            instance = model.objects.get(id=update_fields['id'])
            for attname, val in update_fields.items():
                setattr(instance, attname, val)
            instance.save_base(raw=True)

        self.applied = forward
        self.save()


class auto_track_querysets(object):
    """
    Context manager that will track insert/update/delete for items in a
    QuerySet, and create TrackingSnapshots for all items.
    """
    def __init__(self, querysets, when=lambda: True):
        self.querysets = list(querysets)
        self.when = when

    def __enter__(self):
        self.do_tracking = self.when()
        if not self.do_tracking:
            return
        self.instances = [list(qs.all())
                          for qs in self.querysets]

    def __exit__(self, type, value, traceback):
        if not self.do_tracking:
            return
        for old_instances, qs in zip(self.instances, self.querysets):
            old_instance_dict = {obj.id: obj for obj in old_instances}
            old_ids = set(old_instance_dict.keys())

            new_instance_dict = {obj.id: obj for obj in qs.all()}
            new_ids = set(new_instance_dict.keys())

            for id in old_ids - new_ids:
                TrackingSnapshot.register_delete(old_instance_dict[id])
            for id in new_ids - old_ids:
                TrackingSnapshot.register_insert(new_instance_dict[id])
            for id in old_ids.intersection(new_ids):
                old_instance = old_instance_dict[id]
                new_instance = new_instance_dict[id]
                if get_fields(old_instance) != get_fields(new_instance):
                    TrackingSnapshot.register_update(old_instance, new_instance)


def rewind_models(model, point_in_time):
    path = model_to_path(model)

    # apply unapplied snapshots before point_in_time
    qs1 = (TrackingSnapshot.objects
           .filter(model_path=path,
                   applied=False,
                   created__lte=point_in_time)
           .order_by('created'))
    for ts in qs1:
        ts.apply()

    # unapply applied snapshos before point_in_time.
    # If everything is correct, then only one of these quer
    qs2 = (TrackingSnapshot.objects
           .filter(model_path=path,
                   applied=True,
                   created__gt=point_in_time)
           .order_by('-created'))
    for ts in qs2:
        ts.unapply()


def track_querysets(queryset_callable, when_callable):
    """
    Returns a decorator that wraps a function in an auto_track_querysets context manager.
    Takes two parameters:
    * a callable that takes the function arguments and returns a list of querysets to track
    * a callable that takes the function arguments and returns True if tracking should be enabled.
    """
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            with auto_track_querysets(queryset_callable(*args, **kwargs),
                                      when=lambda: when_callable(*args, **kwargs)):
                return func(*args, **kwargs)
        return decorated
    return decorator


class HttpLog(models.Model):
    response_data = models.TextField()
    request_data = JSONField()
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created']

    def __repr__(self):
        return '<HttpLog {0} {1}>'.format(self.created, self.request.path)

    @classmethod
    def log_request_response(cls, request, response):
        log = HttpLog.objects.create(
            response_data=cls.serialize_response(response),
            request_data=cls.serialize_request(request))
        return log


    @classmethod
    def serialize_response(cls, response):
        return ("HTTP/1.1 {0} {1}\n{2}".format(response.status_code,
                                               response.reason_phrase,
                                               response.serialize())).decode('utf-8')

    @classmethod
    def serialize_request(cls, request):
        retval = {}
        meta = {}
        for k, v in request.META.items():
            if not k.startswith('wsgi.') and not v.__class__.__module__ == 'socket':
                meta[k] = v
        retval['meta'] = meta
        retval['body'] = request.body
        if hasattr(request, 'session'):
            retval['session'] = request.session.items()
        return retval

    @property
    def request(self):
        # Fix environ to fool WSGIRequest
        data = self.request_data
        meta = data['meta']
        body = data['body'].encode('utf-8')
        meta['wsgi.input'] = StringIO(body)
        req = WSGIRequest(meta)
        req._body = body
        if 'session' in data:
            req.session = dict(data['session'])
        return req

    @property
    def response(self):
        return httpparse(self.response_data.encode('utf-8'))


# response parsing:

class FakeSocket():
    def __init__(self, response_str):
        self._file = StringIO(response_str)
    def makefile(self, *args, **kwargs):
        return self._file

def httpparse(response_str):
    socket = FakeSocket(response_str)
    response = HTTPResponse(socket)
    response.begin()
    response.content = response.read(len(response_str))
    response.headers = response.getheaders()
    return response
