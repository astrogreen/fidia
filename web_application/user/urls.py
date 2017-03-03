from django.conf.urls import url
import rest_framework.routers

import user.views


router = rest_framework.routers.SimpleRouter()

# user_list = user.views.UserViewSet.as_view({
#     'get': 'list'
# })
# user_detail = user.views.UserViewSet.as_view({
#     'get': 'retrieve'
# })

urlpatterns = [
    # ADMIN USER VIEW
    # url(r'^users/$', user_list, name='user-list'),
    # url(r'^users/(?P<pk>[0-9]+)/$', user_detail, name='user-detail'),

    # USER ACTIONS
    url(r'^register/', user.views.CreateUserView.as_view(), name='user-register'),
    # url(r'^change-password/', user.views.ChangePasswordView.as_view(), name='user-change-password'),

    # USER PROFILE (restful instance allowing user to update details)
    url(r'^accounts/(?P<username>.+)/$', user.views.UserProfileView.as_view(), name='user-profile-detail'),

]
