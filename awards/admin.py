from django.contrib import admin

from .models import Award


class AwardAdmin(admin.ModelAdmin):

    list_display = ['id', 'account', 'award_type', 'level', 'created']

    def get_queryset(self, request):
        return super(AwardAdmin, self).get_queryset(request).select_related('account')


admin.site.register(Award, AwardAdmin)
