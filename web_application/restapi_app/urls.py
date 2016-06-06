from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import rest_framework.routers

import restapi_app.views


router = rest_framework.routers.SimpleRouter()

# keep users out of the api-root router.register
user_list = restapi_app.views.UserViewSet.as_view({
    'get': 'list'
})
user_detail = restapi_app.views.UserViewSet.as_view({
    'get': 'retrieve'
})

urlpatterns = [
            url(r'^$', TemplateView.as_view(template_name='restapi_app/home/index.html'), name='index'),

            url(r'^(?i)documentation/$',
                      TemplateView.as_view(template_name='restapi_app/documentation/sub-menu.html'),
                      name='documentation'),
            url(r'^(?i)documentation/data-access/$',
                      TemplateView.as_view(template_name='restapi_app/documentation/data-access.html'),
                      name='documentation-data-access'),
            url(r'^(?i)documentation/query-builder/$',
                      TemplateView.as_view(template_name='restapi_app/documentation/query-builder.html'),
                      name='documentation-query-builder'),
            url(r'^(?i)documentation/query-history/$',
              TemplateView.as_view(template_name='restapi_app/documentation/query-history.html'),
              name='documentation-query-history'),
            url(r'^(?i)documentation/schema-browser/$',
              TemplateView.as_view(template_name='restapi_app/documentation/schema-browser.html'),
              name='documentation-schema-browser'),

            url(r'^(?i)under-construction/$',
              TemplateView.as_view(template_name='restapi_app/documentation/underconstruction.html'),
              name='under-construction'),

            url(r'^(?i)about/team/$', TemplateView.as_view(template_name='restapi_app/about/team.html'),
              name='about-team'),

            url(r'^(?i)support/contact/$', restapi_app.views.ContactForm.as_view(), name='support-contact'),

            url(r'^user-testing/feedback/$',
              TemplateView.as_view(template_name='restapi_app/user-testing/feedback.html'),
              name='user-feedback'),
            url(r'^user-testing/feature-tracking/$',
              TemplateView.as_view(template_name='restapi_app/user-testing/feature-tracking.html'),
              name='feature-tracking'),

            url(r'^(?i)signed-out/$', TemplateView.as_view(template_name='restapi_app/user/logout.html'),
              name='logout-page'),

            url(r'^(?i)data/catalogues/', restapi_app.views.AvailableTables.as_view(), name='catalogues'),

            url(r'^users/$', user_list, name='user-list'),
            url(r'^users/(?P<pk>[0-9]+)/$', user_detail, name='user-detail'),

            url(r'^register/', restapi_app.views.CreateUserView.as_view(), name='user-register'),
            url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
