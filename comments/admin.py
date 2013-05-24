from django.contrib import admin

from .models import Comment

class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'created']

    def queryset(self, request):
        return super(CommentAdmin, self).queryset(request).select_related('author')

admin.site.register(Comment, CommentAdmin)
