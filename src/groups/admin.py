from django.contrib import admin

from .models import Group, Invitation, Membership


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "created", "public", "open"]
    autocomplete_fields = ["created_by"]
    readonly_fields = ["slug"]
    search_fields = ["name"]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["account", "group", "created_by"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["account", "group", "created"]
