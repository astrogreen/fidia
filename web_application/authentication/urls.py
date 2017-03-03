from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

import rest_framework.routers
from rest_framework.authtoken import views

import user.forms
router = rest_framework.routers.SimpleRouter()

urlpatterns = [

    # REST_FRAMEWORK USER AUTH
    url(r'', include('user.auth_urls', namespace='rest_framework')),

    # DJANGO AUTH
    url(r'^password-change/$', login_required(auth_views.password_change),
        {'template_name': 'user/django_auth/password-change.html'}, name='password_change'),
    url(r'^password-change/success/$', login_required(auth_views.password_change_done),
        {'template_name': 'user/django_auth/password-change-done.html'}, name='password_change_done'),

    url(r'^password-reset/$', auth_views.password_reset,
        {'password_reset_form': user.forms.EmailValidationPasswordResetForm,
            'template_name': 'user/django_auth/password-reset.html'}, name='password_reset'),
    url(r'^password-reset/success/$', auth_views.password_reset_done,
        {'template_name': 'user/django_auth/password-reset-done.html'}, name='password_reset_done'),

    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, {'template_name': 'user/django_auth/password-reset-confirm.html'},
            name='password_reset_confirm'),

    url(r'^reset/success/', auth_views.password_reset_complete,
        {'template_name': 'user/django_auth/password-reset-complete.html'},
                    name='password_reset_complete'),

    # FETCH TOKEN
    url(r'^api-token-auth/', views.obtain_auth_token)
]
