from rest_framework import pagination, response, serializers

from cms.models import File, Image

from .fields import CanEditField, UpdatedField


class FileSerializer(serializers.HyperlinkedModelSerializer):
    file_url = serializers.ReadOnlyField(source='file.url')
    filename = serializers.ReadOnlyField(source='get_filename')
    can_edit = CanEditField()
    updated = UpdatedField()

    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = ('created', )


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    image_url = serializers.ReadOnlyField(source='image.url')
    thumbnail_url = serializers.ReadOnlyField()
    filename = serializers.ReadOnlyField(source='get_filename')
    size = serializers.ReadOnlyField(source='get_size')
    can_edit = CanEditField()
    updated = UpdatedField()

    class Meta:
        model = Image
        fields = '__all__'
        read_only_fields = ('created', )


class CmsPaginationSerializer(pagination.PageNumberPagination):
    """
    Simple-data-grid expects a total_pages key for a paginated view.
    Simple-data-grid expects rows as the key for objects.
    """
    total_pages = serializers.ReadOnlyField(source='paginator.num_pages')
    results_field = 'rows'
    page_size = 5

    def get_paginated_response(self, data):
        return response.Response({
            'total_pages': self.page.paginator.num_pages,
            'rows': data
        })
