from dal import autocomplete

from .models import Account


class AccountAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        from learnscripture.views import account_from_request

        account = account_from_request(self.request)
        qs = Account.objects.visible_for_account(account, exclude_hellbanned=True)

        if self.q:
            qs = (
                qs.filter(username__istartswith=self.q)
                | qs.filter(first_name__istartswith=self.q)
                | qs.filter(last_name__istartswith=self.q)
            )
        return qs
