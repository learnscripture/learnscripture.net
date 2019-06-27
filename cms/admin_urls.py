from django.conf.urls import url

from . import admin_views

urlpatterns = [
    url(r'^page/(?P<id>\d+)/move_up/$', admin_views.page_move_up, name='cms_page_move_up'),
    url(r'^page/(?P<id>\d+)/move_down/$', admin_views.page_move_down, name='cms_page_move_down'),
]
