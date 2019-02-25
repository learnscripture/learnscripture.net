from django.contrib import admin

from .models import SiteNotice


class SiteNoticeAdmin(admin.ModelAdmin):
    list_display = [
        'message_html',
        'language_code',
        'is_active',
        'begins',
        'ends',
    ]


admin.site.register(SiteNotice, SiteNoticeAdmin)
