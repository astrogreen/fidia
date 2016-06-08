from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import rest_framework.routers

import user.views


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
            # url(r'^users/(?P<username>.+)/$', user_detail, name='user-detail'),

            url(r'^register/', user.views.CreateUserView.as_view(), name='user-register'),
            url(r'^sign-out/$', TemplateView.as_view(template_name='user/logout/logout.html'), name='logout-page'),
            url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),

            # USER PROFILE
            url(r'^profile/(?P<username>.+)/$', user.views.UserProfileView.as_view(), name='user-profile-detail')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
