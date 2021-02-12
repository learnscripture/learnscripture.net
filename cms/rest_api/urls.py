from django.urls import path

from . import views

urlpatterns = [
    path('', views.api_root),
    path('images/', views.ImageList.as_view(), name='image-list'),
    path('images/<int:pk>/', views.ImageDetail.as_view(), name='image-detail'),
    path('files/', views.FileList.as_view(), name='file-list'),
    path('files/<int:pk>/', views.FileDetail.as_view(), name='file-detail'),
]
