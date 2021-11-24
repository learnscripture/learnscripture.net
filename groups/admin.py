from django.contrib import admin

from .models import Group, Invitation, Membership


class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "created", "public", "open"]
    readonly_fields = ["slug"]
    search_fields = ["name"]


class InvitationAdmin(admin.ModelAdmin):
    list_display = ["account", "group", "created_by"]


class MembershipAdmin(admin.ModelAdmin):
    list_display = ["account", "group", "created"]


admin.site.register(Group, GroupAdmin)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(Membership, MembershipAdmin)
