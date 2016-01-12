from django.conf.urls import url, include
from restapi_app import views
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from restapi_app.routers import ExtendDefaultRouter, ExtendNestedRouter
from rest_framework_extensions.routers import ExtendedSimpleRouter
from rest_framework_extensions.routers import ExtendedDefaultRouter

# Create a router and register our viewsets with it.

router_nest = ExtendNestedRouter()
router_back = ExtendNestedRouter()

router_nest\
    .register(r'survey', views.SurveyViewSet, base_name='survey')\
    .register(r'version', views.VersionViewSet, base_name='version', parents_query_lookups=['survey_id'])

router_back\
    .register(r'version', views.VersionViewSet, base_name='version')\
    .register(r'survey', views.SurveyViewSet, base_name='survey', parents_query_lookups=['version_id'])


#   = = = = = =
router = ExtendDefaultRouter()
router.register(r'query', views.QueryViewSet),
router.register(r'users', views.UserViewSet),
# router.register(r'surveys', views.SurveyViewSet)
# router.register(r'version', views.VersionViewSet)

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
urlpatterns = [
    url(r'^data/', include(router.urls)),
    # url(r'^data/', include(router_nest.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^home/', TemplateView.as_view(template_name='restapi_app/web_only/index.html'), name='index'),
]

urlpatterns += router_nest.urls
urlpatterns += router_back.urls


