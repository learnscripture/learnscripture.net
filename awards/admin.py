from django.contrib import admin

from .models import Award


@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):

    list_display = ["id", "account", "award_type", "level", "created"]
    list_filter = ["award_type", "level"]
    search_fields = ["account__username"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("account")
