from django.contrib import admin

from .models import Comment


class CommentAdmin(admin.ModelAdmin):
    list_display = ["message", "author", "created", "hidden"]
    raw_id_fields = ["event"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author")


admin.site.register(Comment, CommentAdmin)
