from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

import rest_framework.routers

import user.views
import user.auth_urls
import user.forms


router = rest_framework.routers.SimpleRouter()

user_list = user.views.UserViewSet.as_view({
    'get': 'list'
})
user_detail = user.views.UserViewSet.as_view({
    'get': 'retrieve'
})

urlpatterns = [
            # ADMIN USER VIEW
            url(r'^users/$', user_list, name='user-list'),
            url(r'^users/(?P<pk>[0-9]+)/$', user_detail, name='user-detail'),

            # USER ACTIONS
            url(r'^register/', user.views.CreateUserView.as_view(), name='user-register'),
            url(r'^change-password/', user.views.ChangePasswordView.as_view(), name='user-change-password'),

            # REST_FRAMEWORK USER AUTH
            url(r'', include('user.auth_urls', namespace='rest_framework')),

            # USER PROFILE (restful instance allowing user to update details)
            url(r'^profile/(?P<username>.+)/$', user.views.UserProfileView.as_view(), name='user-profile-detail'),
            # url(r'^change-password/(?P<username>.+)/$', user.views.UserUpdatePasswordView.as_view(), name='user-change-password-detail'),


            # DJANGO AUTH
            # url('^', include('django.contrib.auth.urls')),

            # url(r'^cp/', auth_views.password_change, {'template_name': 'user/django_auth/change-password.html'} )
            url(r'^password-change/', auth_views.password_change, name='password_change'),
            url(r'^password-change/success', auth_views.password_change_done, name='password_change_done'),
            url(r'^password-reset/', auth_views.password_reset, {'password_reset_form': user.forms.EmailValidationPasswordResetForm}, name='password_reset'),
            url(r'^password-reset/success', auth_views.password_reset_done, name='password_reset_done'),
            url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.password_reset_confirm, name='password_reset_confirm'),
            url(r'^reset/done/', auth_views.password_reset_complete, name='password_reset_complete'),


            #     REST API NAMESPACED
            # ^login/$ [name='login']
            # ^logout/$ [name='logout']
            #     MANAGED BY DJANGO (not restful endpoints)
            # ^password_change/$ [name='password_change']
            # ^password_change/done/$ [name='password_change_done']
            # ^password_reset/$ [name='password_reset']
            # ^password_reset/done/$ [name='password_reset_done']
            # ^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$ [name='password_reset_confirm']
            # ^reset/done/$ [name='password_reset_complete']



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
