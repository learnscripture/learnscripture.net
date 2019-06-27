from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.api_root),
    url(r'^images/$', views.ImageList.as_view(), name='image-list'),
    url(r'^images/(?P<pk>[^/]+)/$', views.ImageDetail.as_view(), name='image-detail'),
    url(r'^files/$', views.FileList.as_view(), name='file-list'),
    url(r'^files/(?P<pk>[^/]+)/$', views.FileDetail.as_view(), name='file-detail'),
]
