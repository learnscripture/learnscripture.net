from django.contrib import admin
from accounts.models import notify_all_identities, notify_all_accounts

from .models import SiteNotice


def make_convert_to_individual_notices(notify_function, name, description):
    def convert_to_individual_notices(modeladmin, request, queryset):
        for notice in queryset:
            notify_all_identities(notice.language_code, notice.message_html)
        queryset.update(is_active=False)
    convert_to_individual_notices.__name__ = name
    convert_to_individual_notices.short_description = description
    return convert_to_individual_notices


convert_to_individual_notices_identities = make_convert_to_individual_notices(
    notify_all_identities,
    "convert_to_individual_notices_identities",
    "Convert to individual notices - all identities"
)
convert_to_individual_notices_accounts = make_convert_to_individual_notices(
    notify_all_accounts,
    "convert_to_individual_notices_accounts",
    "Convert to individual notices - all accounts"
)


class SiteNoticeAdmin(admin.ModelAdmin):
    list_display = [
        'message_html',
        'language_code',
        'is_active',
        'begins',
        'ends',
    ]
    actions = [
        convert_to_individual_notices_identities,
        convert_to_individual_notices_accounts,
    ]


admin.site.register(SiteNotice, SiteNoticeAdmin)
