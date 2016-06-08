from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import rest_framework.routers

from restapi_app.routers import ExtendDefaultRouter, NestedExtendDefaultRouter

import data_browser.views

router = rest_framework.routers.SimpleRouter()
# router = ExtendDefaultRouter()

router.register(r'gama', data_browser.views.GAMAViewSet, base_name='gama')
router.register(r'sami', data_browser.views.SAMIViewSet, base_name='sami')

# router.register(r'testing/(?P<dynamic_pk>.+)', data_browser.views.TestingViewSet, base_name='testing')

# Nested routes for sample (SAMI)
object_nested_router = NestedExtendDefaultRouter(router, r'sami', lookup='sami')
object_nested_router.register(r'(?P<galaxy_pk>[^/.]+)', data_browser.views.AstroObjectViewSet, base_name='galaxy')

trait_nested_router = NestedExtendDefaultRouter(object_nested_router, r'(?P<galaxy_pk>[^/.]+)', lookup='galaxy')
trait_nested_router.register(r'(?P<trait_pk>[^/.]+)', data_browser.views.TraitViewSet, base_name='trait')

# traitprop_nested_router = NestedExtendDefaultRouter(trait_nested_router, r'(?P<trait_pk>[^/.]+)', lookup='trait')
# traitprop_nested_router.register(r'(?P<traitproperty_pk>[^/.]+)', data_browser.views.TraitPropertyViewSet, base_name='traitproperty')

sub_traitprop_nested_router = NestedExtendDefaultRouter(trait_nested_router, r'(?P<trait_pk>[^/.]+)', lookup='trait')
sub_traitprop_nested_router.register(r'(?P<dynamic_pk>.+)', data_browser.views.SubTraitPropertyViewSet, base_name='traitproperty')


urlpatterns = [
    url(r'^(?i)', include(router.urls)),
    url(r'^(?i)', include(object_nested_router.urls)),
    url(r'^(?i)', include(trait_nested_router.urls)),
    # url(r'^(?i)', include(traitprop_nested_router.urls)),
    url(r'^(?i)', include(sub_traitprop_nested_router.urls)),
    url(r'^(?i)checkout/', data_browser.views.Checkout.as_view(), name='checkout'),
    url(r'^sandbox/$', TemplateView.as_view(template_name='data_browser/sandbox/sandbox.html'), name='sandbox'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
