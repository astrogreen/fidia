from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import rest_framework.routers

from restapi_app.routers import ExtendDefaultRouter, NestedExtendDefaultRouter
from fidia.traits.trait_key import TRAIT_KEY_RE

import data_browser.views

router = rest_framework.routers.SimpleRouter()
# router = ExtendDefaultRouter()

router.register(r'data-browser', data_browser.views.DataBrowserViewSet, base_name='data-browser')

# Nested routes for sample (SAMI)
sample_nested_router = NestedExtendDefaultRouter(router, r'data-browser', lookup='data-browser')
sample_nested_router.register(r'(?P<sample_pk>[^/]+)', data_browser.views.SampleViewSet, base_name='sample')

object_nested_router = NestedExtendDefaultRouter(sample_nested_router, r'(?P<sample_pk>[^/]+)', lookup='sample')
object_nested_router.register(r'(?P<astroobject_pk>[^/]+)', data_browser.views.AstroObjectViewSet, base_name='astroobject')

trait_nested_router = NestedExtendDefaultRouter(object_nested_router, r'(?P<astroobject_pk>[^/]+)', lookup='astroobject')
trait_nested_router.register(r'(?P<trait_pk>[^/]+)', data_browser.views.TraitViewSet, base_name='trait')
# trait_key_pattern = '(?P<trait_type>[a-zA-Z][a-zA-Z0-9_]*)(?:-(?P<trait_qualifier>[a-zA-Z0-9][a-zA-Z0-9_.]*))?(?:[:](?P<branch>[a-zA-Z0-9][a-zA-Z0-9_.]*))?(?:\((?P<version>[a-zA-Z0-9][a-zA-Z0-9_.]*)\))?'
trait_nested_router.register(r'(?P<trait_pk>' + TRAIT_KEY_RE.pattern + ')', data_browser.views.TraitViewSet, base_name='trait')

# traitprop_nested_router = NestedExtendDefaultRouter(trait_nested_router, r'(?P<trait_pk>[^/.]+)', lookup='trait')
# traitprop_nested_router.register(r'(?P<traitproperty_pk>[^/.]+)', data_browser.views.TraitPropertyViewSet, base_name='traitproperty')

sub_traitprop_nested_router = NestedExtendDefaultRouter(trait_nested_router, r'(?P<trait_pk>[^/]+)', lookup='trait')
sub_traitprop_nested_router.register(r'(?P<subtraitproperty_pk>[^/]+)', data_browser.views.SubTraitPropertyViewSet, base_name='subtraitproperty')

traitprop_nested_router = NestedExtendDefaultRouter(sub_traitprop_nested_router, r'(?P<subtraitproperty_pk>[^/]+)', lookup='subtraitproperty')
traitprop_nested_router.register(r'(?P<traitproperty_pk>[^/]+)', data_browser.views.TraitPropertyViewSet, base_name='traitproperty')


# sub_traitprop_nested_router = NestedExtendDefaultRouter(trait_nested_router, r'(?P<trait_pk>[^/]+)', lookup='trait')
# sub_traitprop_nested_router.register(r'(?P<dynamic_pk>.+)', data_browser.views.DynamicViewSet, base_name='subtraitproperty')


urlpatterns = [
    url(r'^(?i)', include(router.urls)),
    url(r'^(?i)', include(sample_nested_router.urls)),
    url(r'^(?i)', include(object_nested_router.urls)),
    url(r'^(?i)', include(trait_nested_router.urls)),
    # url(r'^(?i)', include(traitprop_nested_router.urls)),
    url(r'^(?i)', include(sub_traitprop_nested_router.urls)),
    url(r'^(?i)', include(traitprop_nested_router.urls)),

]