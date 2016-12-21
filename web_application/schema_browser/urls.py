from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import rest_framework.routers

from restapi_app.routers import NestedExtendDefaultRouter

from fidia.traits.trait_key import TRAIT_KEY_RE

import schema_browser.views

router = rest_framework.routers.SimpleRouter()
# router = ExtendDefaultRouter()

router.register(r'schema-browser', schema_browser.views.SchemaViewSet, base_name='root')

# Nested routes for sample ()
survey_nested_router = NestedExtendDefaultRouter(router, r'schema-browser', lookup='root')
survey_nested_router.register(r'(?P<survey_pk>[^/]+)', schema_browser.views.SurveyViewSet, base_name='survey')

trait_nested_router = NestedExtendDefaultRouter(survey_nested_router, r'(?P<survey_pk>[^/]+)', lookup='survey')
trait_nested_router.register(r'(?P<trait_pk>[^/]+)', schema_browser.views.TraitViewSet, base_name='trait')

dynamic_nested_router = NestedExtendDefaultRouter(trait_nested_router, r'(?P<trait_pk>[^/]+)', lookup='trait')
dynamic_nested_router.register(r'(?P<dynamic_pk>.*)', schema_browser.views.DynamicViewSet, base_name='dynamic')
# dynamic_nested_router.register(r'(?P<dynamic_pk>(.*)' + TRAIT_KEY_RE.pattern + ')', schema_browser.views.DynamicViewSet,
#                                base_name='dynamic')

urlpatterns = [
    url(r'^(?i)', include(router.urls)),
    url(r'^(?i)', include(survey_nested_router.urls)),
    url(r'^(?i)', include(trait_nested_router.urls)),
    url(r'^(?i)', include(dynamic_nested_router.urls)),
]


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
