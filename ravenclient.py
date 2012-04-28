# Outside learnscripture/ to avoid import cycles

from raven.contrib.django import DjangoClient
from raven.contrib.async import AsyncClient

class AsyncDjangoClient(AsyncClient, DjangoClient):
    pass
