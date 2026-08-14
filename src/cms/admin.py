from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied
from django.utils.html import format_html, format_html_join
from mptt.admin import MPTTModelAdmin
from sql_util.utils import Exists

from . import admin_forms as forms
from .models import Content, ContentItem, File, Image, Page, PageContentItem, PageTitle
from .utils.fields import CmsHTMLField
from .utils.widgets import AdminImageWidgetWithPreview, CmsTextarea


class ContentInline(admin.StackedInline):
    model = Content
    extra = 1
    formfield_overrides = {CmsHTMLField: {"widget": CmsTextarea}}
    min_num = 1


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "used"]
    list_display_links = ["id", "name"]
    date_hierarchy = "updated"
    search_fields = ["name", "content_set__content_html"]
    inlines = [ContentInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(used=Exists("page_content_items"))

    @admin.display(boolean=True)
    def used(self, obj):
        return obj.used


class PageContentItemInline(admin.TabularInline):
    model = PageContentItem
    extra = 1

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("sort")


class PageTitleInline(admin.TabularInline):
    model = PageTitle
    extra = 1
    min_num = 1


@admin.register(Page)
class PageAdmin(MPTTModelAdmin):
    form = forms.PageForm
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "parent",
                    "url",
                    "redirect_page",
                    "template_name",
                    "is_public",
                )
            },
        ),
    )

    inlines = [PageTitleInline, PageContentItemInline]
    list_display = ("url", "view_on_site_link", "redirect_page", "is_public", "action_links")
    list_per_page = 1000
    search_fields = ("url", "titles__title")

    @admin.display(description="")
    def view_on_site_link(self, page):
        absolute_url = page.get_absolute_url()
        if not absolute_url:
            return ""
        return format_html(
            '<a href="{0}" title="{1}" target="_blank"><img src="{2}cms/admin/images/world.gif" width="16" height="16" alt="{3}" /></a>',
            absolute_url,
            "View on site",
            settings.STATIC_URL,
            "View on site",
        )

    @admin.display(description="Actions")
    def action_links(self, page):
        actions = []

        # first child cannot be moved up, last child cannot be moved down
        if not page.is_first_child():
            actions.append(
                format_html(
                    '<a href="{0}/move_up/" title="{1}"><img src="{2}cms/admin/images/arrow_up.gif" width="16" height="16" alt="{3}" /></a> ',
                    page.pk,
                    "Move up",
                    settings.STATIC_URL,
                    "Move up",
                )
            )
        else:
            actions.append(
                format_html(
                    '<img src="{0}cms/admin/images/blank.gif" width="16" height="16" alt="" /> ', settings.STATIC_URL
                )
            )

        if not page.is_last_child():
            actions.append(
                format_html(
                    '<a href="{0}/move_down/" title="{1}"><img src="{2}cms/admin/images/arrow_down.gif" width="16" height="16" alt="{3}" /></a> ',
                    page.pk,
                    "Move down",
                    settings.STATIC_URL,
                    "Move down",
                )
            )
        else:
            actions.append(
                format_html(
                    '<img src="{0}cms/admin/images/blank.gif" width="16" height="16" alt="" /> ', settings.STATIC_URL
                )
            )

        # add subpage
        actions.append(
            format_html(
                '<a href="add/?{0}={1}" title="{2}"><img src="{3}cms/admin/images/page_new.gif" width="16" height="16" alt="{4}" /></a> ',
                self.model._mptt_meta.parent_attr,
                page.pk,
                "Add sub page",
                settings.STATIC_URL,
                "Add sub page",
            )
        )

        return format_html('<span class="nobr">{0}</span>', format_html_join("", "{0}", ((a,) for a in actions)))

    def save_model(self, request, obj, form, change):
        """
        - Optionally positions a Page `obj` before or beneath another page, based on POST data.
        - Notifies the PERMISSION_CLASS that a Page was created by `user`.
        """
        if "before_page_id" in request.POST:
            before_page = Page.objects.get(pk=int(request.POST["before_page_id"]))
            obj.parent = before_page.parent
            obj.insert_at(before_page, position="left", save=False)
        elif "below_page_id" in request.POST:
            below_page = Page.objects.get(pk=int(request.POST["below_page_id"]))
            obj.parent = below_page
            obj.insert_at(below_page, position="last-child", save=False)

        super().save_model(request, obj, form, change)


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "title",
        "updated",
    )
    date_hierarchy = "updated"
    search_fields = ("title",)
    actions = ["really_delete_selected"]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions[
                "delete_selected"
            ]  # the original delete selected action doesn't remove associated files, because .delete() is never called
        return actions

    @admin.action(description="Delete selected files")
    def really_delete_selected(self, request, queryset):
        deleted_count = 0

        # Check that the user has delete permission for the actual model
        if not self.has_delete_permission(request):
            raise PermissionDenied

        for obj in queryset:
            obj.delete()
            deleted_count += 1

        if deleted_count:
            messages.add_message(
                request,
                messages.INFO,
                f"Successfully deleted {deleted_count} {model_ngettext(self.opts, deleted_count)}.",
            )


@admin.register(Image)
class ImageAdmin(FileAdmin):
    list_display = (
        "preview",
        "__str__",
        "title",
        "get_size",
        "updated",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "image",
                    "title",
                )
            },
        ),
        (
            "Size",
            {
                "classes": ("collapse",),
                "fields": (
                    "width",
                    "height",
                ),
            },
        ),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == "image":
            kwargs.pop("request", None)
            kwargs["widget"] = AdminImageWidgetWithPreview
            return db_field.formfield(**kwargs)
        return super().formfield_for_dbfield(db_field, **kwargs)
