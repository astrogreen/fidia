from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import rest_framework.routers

from restapi_app.routers import ExtendDefaultRouter, NestedExtendDefaultRouter
# from fidia.traits.trait_key import TRAIT_KEY_RE

import sov.views

router = rest_framework.routers.SimpleRouter()
router.register(r'astro-objects', sov.views.AstroObject, base_name='astro-object')
router.register(r'surveys', sov.views.Survey, base_name='survey')

# router.register(r'sov', sov.views.RootViewSet, base_name='root')

# Nested routes for survey (SAMI)
# survey_nested_router = NestedExtendDefaultRouter(router, r'sov', lookup='root')
# survey_nested_router.register(r'(?P<survey_pk>[^/]+)', sov.views.SurveyViewSet, base_name='survey')
#
# object_nested_router = NestedExtendDefaultRouter(survey_nested_router, r'(?P<survey_pk>[^/]+)', lookup='survey')
# object_nested_router.register(r'(?P<astroobject_pk>[^/]+)', sov.views.AstroObjectViewSet, base_name='astroobject')
#
# trait_nested_router = NestedExtendDefaultRouter(object_nested_router, r'(?P<astroobject_pk>[^/]+)', lookup='astroobject')
# trait_nested_router.register(r'(?P<trait_pk>[^/]+)', sov.views.TraitViewSet, base_name='trait')
# trait_nested_router.register(r'(?P<trait_pk>' + TRAIT_KEY_RE.pattern + ')', sov.views.TraitViewSet, base_name='trait')
#
# sub_traitprop_nested_router = NestedExtendDefaultRouter(trait_nested_router, r'(?P<trait_pk>[^/]+)', lookup='trait')
# sub_traitprop_nested_router.register(r'(?P<subtraitproperty_pk>[^/]+)', sov.views.SubTraitPropertyViewSet, base_name='subtraitproperty')
#
# traitprop_nested_router = NestedExtendDefaultRouter(sub_traitprop_nested_router, r'(?P<subtraitproperty_pk>[^/]+)', lookup='subtraitproperty')
# traitprop_nested_router.register(r'(?P<traitproperty_pk>[^/]+)', sov.views.TraitPropertyViewSet, base_name='traitproperty')


urlpatterns = [
    # url(r'^surveys/$', sov.views.Surveys.as_view(), name='survey'),
    # url(r'^surveys/(?:(?P<survey_name>[\w]+)/?)?$', sov.views.Survey.as_view(), name='survey'),

    # url(r'^astro-objects/$', sov.views.AstroObjects.as_view(), name='astro-objects'),
    # url(r'^astro-objects/(?:(?P<astro_object_name>[\w]+)/?)?$', sov.views.AstroObjects.as_view(), name='astro-objects'),

    url(r'', include(router.urls)),
    url(r'^data-for/$', sov.views.DataFor.as_view(), name='data'),
    url(r'^data-for/(?:(?P<object_type>[\w]+)/?)?$', sov.views.DataForType.as_view(), name='data-for'),

    url(r'^schema-for/$', sov.views.SchemaFor.as_view(), name='schema'),
    url(r'^schema-for/(?:(?P<object_type>[\w]+)/?)?$', sov.views.SchemaForType.as_view(), name='schema-for'),


    # url(r'^(?i)', include(router.urls)),
    # url(r'^(?i)', include(survey_nested_router.urls)),
    # url(r'^(?i)', include(object_nested_router.urls)),
    # url(r'^(?i)', include(trait_nested_router.urls)),
    # url(r'^(?i)', include(sub_traitprop_nested_router.urls)),
    # url(r'^(?i)', include(traitprop_nested_router.urls)),
]