from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import rest_framework.routers

from restapi_app.routers import NestedExtendDefaultRouter

from fidia.traits.trait_key import TRAIT_KEY_RE

import schema.views

router = rest_framework.routers.SimpleRouter()
# router = ExtendDefaultRouter()

router.register(r'schema', schema.views.SchemaViewSet, base_name='schema')

# router.register(r'testing/(?P<dynamic_pk>.+)', data_browser.views.TestingViewSet, base_name='testing')

# Nested routes for sample ()
sample_nested_router = NestedExtendDefaultRouter(router, r'schema', lookup='schema')
sample_nested_router.register(r'(?P<sample_pk>[^/]+)', schema.views.SampleViewSet, base_name='sample')

astroobject_nested_router = NestedExtendDefaultRouter(sample_nested_router, r'(?P<sample_pk>[^/]+)', lookup='sample')
astroobject_nested_router.register(r'(?P<astroobject_pk>[^/]+)', schema.views.AstroObjectViewSet, base_name='astroobject')

trait_nested_router = NestedExtendDefaultRouter(astroobject_nested_router, r'(?P<astroobject_pk>[^/]+)', lookup='astroobject')
trait_nested_router.register(r'(?P<trait_pk>[^/]+)', schema.views.TraitViewSet, base_name='trait')
trait_nested_router.register(r'(?P<trait_pk>' + TRAIT_KEY_RE.pattern + ')', schema.views.TraitViewSet, base_name='trait')

# traitprop_nested_router = NestedExtendDefaultRouter(trait_nested_router, r'(?P<trait_pk>[^/.]+)', lookup='trait')
# traitprop_nested_router.register(r'(?P<traitproperty_pk>[^/.]+)', data_browser.views.TraitPropertyViewSet, base_name='traitproperty')

subtraitprop_nested_router = NestedExtendDefaultRouter(trait_nested_router, r'(?P<trait_pk>[^/]+)', lookup='trait')
subtraitprop_nested_router.register(r'(?P<dynamic_pk>.+)', schema.views.SubTraitPropertyViewSet, base_name='subtraitproperty')


urlpatterns = [
    url(r'^(?i)', include(router.urls)),
    url(r'^(?i)', include(sample_nested_router.urls)),
    url(r'^(?i)', include(astroobject_nested_router.urls)),
    url(r'^(?i)', include(trait_nested_router.urls)),
    # url(r'^(?i)', include(traitprop_nested_router.urls)),
    url(r'^(?i)', include(subtraitprop_nested_router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
