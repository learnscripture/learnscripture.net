# Outside learnscripture/ to avoid import cycles

from raven.contrib.django import DjangoClient
from raven.contrib.async import AsyncWorker


# AsyncClient in Raven currently has a critical bug - it calls self.worker.queue
# resulting in "Queue instance has no __call__ method".  Plus we need a subclass
# that uses DjangoClient.

class AsyncDjangoClient(DjangoClient):
    """
    This client uses a single background thread to dispatch errors.
    """
    def __init__(self, *args, **kwargs):
        self.worker = AsyncWorker()
        super(AsyncDjangoClient, self).__init__(*args, **kwargs)

    def send_sync(self, **kwargs):
        super(AsyncDjangoClient, self).send(**kwargs)

    def send(self, **kwargs):
        self.worker.queue.put_nowait((self.send_sync, kwargs))
