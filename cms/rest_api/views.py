import six
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.utils.encoding import smart_text
from rest_framework import generics, permissions, renderers, status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse

from cms.models import File, Image

from .serializers import CmsPaginationSerializer, FileSerializer, ImageSerializer

API_RENDERERS = (renderers.JSONRenderer, )

_403_FORBIDDEN_RESPONSE = Response(
    {
        'detail': 'You do not have permission to access this resource. ' +
        'You may need to login or otherwise authenticate the request.'
    },
    status.HTTP_403_FORBIDDEN)


class PlainText(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        if isinstance(data, six.string_types):
            return data
        return smart_text(data)


class CmsListCreateAPIView(generics.ListCreateAPIView):
    pass


class FileList(CmsListCreateAPIView):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    renderer_classes = API_RENDERERS
    permission_classes = (permissions.IsAdminUser,)

    pagination_class = CmsPaginationSerializer

    orderable_fields = ('filename', 'updated')

    def check_fields(self, order_by):
        if order_by not in self.orderable_fields:
            return Response("Can not order by the passed value.", status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        qs = super(FileList, self).get_queryset(*args, **kwargs)
        search = self.request.query_params.get('search')

        if search:
            qs = qs.filter(file__icontains=search)

        order_by = self.request.query_params.get('order_by', 'updated')
        self.check_fields(order_by)

        if order_by == 'filename':
            order_by = 'file'

        sort_order = self.request.query_params.get('sortorder', 'asc')

        qs = qs.order_by(f"{'-' if sort_order != 'asc' else ''}{order_by}")

        return qs


class FileDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    renderer_classes = API_RENDERERS
    permission_classes = (permissions.IsAdminUser,)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        file_name = obj.get_filename()
        delete_response = ''

        if not request.user.has_perm('cms.delete_image'):
            delete_response = f"You don't have permission to delete {file_name}."
            return Response(delete_response, status=403)

        try:
            obj.delete()
            delete_response = f"Successfully deleted {file_name}."
        except ProtectedError:
            delete_response = "%(file_name)s is not deleted, because that would require deleting protected related objects." % {
                'file_name': file_name
            }

        return Response(delete_response, status=200)


class ImageList(CmsListCreateAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    renderer_classes = API_RENDERERS
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = CmsPaginationSerializer
    orderable_fields = ('filename', 'size', 'updated')

    def check_fields(self, order_by):
        if order_by not in self.orderable_fields:
            return Response("Can not order by the passed value.", status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        qs = super(ImageList, self).get_queryset(*args, **kwargs)
        search = self.request.query_params.get('search')
        if search:
            # TODO: image_icontains searches in the entire path, it should only search in the filename (use iregex for this?)
            qs = qs.filter(Q(image__icontains=search) | Q(title__icontains=search) | Q(width__icontains=search) | Q(height__icontains=search))

        order_by = self.request.query_params.get('order_by', 'updated')
        self.check_fields(order_by)

        if order_by == 'filename':
            order_by = 'image'
        elif order_by == 'size':
            order_by = 'width'

        sort_order = self.request.query_params.get('sortorder', 'asc')

        qs = qs.order_by(f"{'-' if sort_order != 'asc' else ''}{order_by}")

        return qs


class ImageDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    renderer_classes = API_RENDERERS
    permission_classes = (permissions.IsAdminUser,)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        file_name = obj.get_filename()
        delete_response = ''

        if not request.user.has_perm('cms.delete_image'):
            delete_response = f"You don't have permission to delete {file_name}."
            return Response(delete_response, status=403)

        try:
            obj.delete()
            delete_response = f"Successfully deleted {file_name}."
        except ProtectedError:
            delete_response = "%(file_name)s is not deleted, because that would require deleting protected related objects." % {
                'file_name': file_name
            }

        return Response(delete_response, status=200)


@api_view(('GET',))
@renderer_classes(API_RENDERERS)
@permission_classes((permissions.IsAdminUser, ))
def api_root(request, format='None'):
    """
    This is the entry point for the API.
    """
    return Response({
        'images': reverse('image-list', request=request),
        'files': reverse('file-list', request=request),
    })
