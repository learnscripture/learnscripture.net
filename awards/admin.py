from django.contrib import admin
from .models import Award


class AwardAdmin(admin.ModelAdmin):

    list_display = ['id', 'account', 'award_type', 'level', 'created']

    def queryset(self, request):
        return super(AwardAdmin, self).queryset(request).select_related('account')


admin.site.register(Award, AwardAdmin)
