"""
Login and logout views for the browsable API.

Add these to your root URLconf if you're using the browsable API and
your API requires authentication:

    urlpatterns = [
        ...
        url(r'^auth/', include('rest_framework.urls', namespace='rest_framework'))
    ]

In Django versions older than 1.9, the urls must be namespaced as 'rest_framework',
and you should make sure your authentication settings include `SessionAuthentication`.
"""
from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.auth import views

app_name = 'rest_framework'
urlpatterns = [
    url(r'^sign-in/$', views.login, {'template_name': 'user/django_auth/login.html'}, name='login'),
    url(r'^sign-out/$', views.logout, {'template_name': 'user/django_auth/logout.html'}, name='logout'),
]
