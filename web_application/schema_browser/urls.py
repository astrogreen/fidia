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
sample_nested_router = NestedExtendDefaultRouter(router, r'schema-browser', lookup='root')
sample_nested_router.register(r'(?P<survey_pk>[^/]+)', schema_browser.views.SurveyViewSet, base_name='survey-browser')

# astroobject_nested_router = NestedExtendDefaultRouter(sample_nested_router, r'(?P<survey_pk>[^/]+)', lookup='sample')
# astroobject_nested_router.register(r'(?P<astroobject_pk>[^/]+)', schema.views.AstroObjectViewSet, base_name='astroobject')
#
# trait_nested_router = NestedExtendDefaultRouter(astroobject_nested_router, r'(?P<astroobject_pk>[^/]+)', lookup='astroobject')
# trait_nested_router.register(r'(?P<trait_pk>[^/]+)', schema.views.TraitViewSet, base_name='trait')
# trait_nested_router.register(r'(?P<trait_pk>' + TRAIT_KEY_RE.pattern + ')', schema.views.TraitViewSet, base_name='trait')

urlpatterns = [
    url(r'^(?i)', include(router.urls)),
    url(r'^(?i)', include(sample_nested_router.urls)),
    # url(r'^(?i)', include(astroobject_nested_router.urls)),
    # url(r'^(?i)', include(trait_nested_router.urls)),
]


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
