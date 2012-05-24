from selectable.base import ModelLookup
from selectable.registry import registry

from .models import Account

class AccountLookup(ModelLookup):
    model = Account
    search_fields = ('username__startswith',
                     'first_name__startswith',
                     'last_name__startswith',
                     )


registry.register(AccountLookup)
