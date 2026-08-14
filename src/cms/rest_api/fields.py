from django.contrib.humanize.templatetags.humanize import naturaltime
from rest_framework import serializers


class CanEditField(serializers.ReadOnlyField):
    """
    A custom field that returns True if request.user has
    permission to edit obj.
    """

    def to_representation(self, value):
        return self.context["request"].user.is_superuser


class UpdatedField(serializers.ReadOnlyField):
    """
    Return a friendly timestamp.
    """

    def to_representation(self, value):
        return naturaltime(value)
