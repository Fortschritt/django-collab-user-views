from django.conf.urls import url

from . import views

app_name = 'collab_user_views'
urlpatterns = [
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^create_space/$', views.create_space, name='create_space'),
    url(r'^help/$', views.help, name='help'),
]