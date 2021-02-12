from django.urls import path

from . import admin_views

urlpatterns = [
    path('page/<int:id>/move_up/', admin_views.page_move_up, name='cms_page_move_up'),
    path('page/<int:id>/move_down/', admin_views.page_move_down, name='cms_page_move_down'),
]
