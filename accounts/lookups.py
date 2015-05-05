from selectable.base import ModelLookup
from selectable.registry import registry

from .models import Account


class AccountLookup(ModelLookup):
    model = Account
    search_fields = ('username__istartswith',
                     'first_name__istartswith',
                     'last_name__istartswith',
                     )


registry.register(AccountLookup)
