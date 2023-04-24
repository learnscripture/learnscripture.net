from django import forms
from django.contrib import admin

from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = "__all__"
        widgets = {
            "message": forms.Textarea(attrs={"cols": 80, "rows": 20}),
        }


class CommentAdmin(admin.ModelAdmin):
    list_display = ["message", "author", "created", "hidden"]
    autocomplete_fields = ["author", "group"]
    search_fields = ["id"]
    raw_id_fields = ["event"]
    form = CommentForm

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author")


admin.site.register(Comment, CommentAdmin)
