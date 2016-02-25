from django.conf.urls import url, include
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import SimpleRouter

from django.views.generic import TemplateView
from .routers import ExtendDefaultRouter, NestedExtendDefaultRouter
from django.conf import settings
from django.conf.urls.static import static

router = ExtendDefaultRouter()

router.register(r'query', views.QueryViewSet),
router.register(r'users', views.UserViewSet),
router.register(r'SOV', views.SOVViewSet),

router.register(r'surveys', views.SurveyViewSet),
router.register(r'releases', views.ReleaseTypeViewSet),
router.register(r'catalogues', views.CatalogueViewSet),
router.register(r'cataloguegroups', views.CatalogueGroupViewSet),
router.register(r'imaging', views.ImageViewSet),
router.register(r'spectra', views.SpectraViewSet),
router.register(r'astro', views.AstroObjectViewSet, base_name='astro')

router.register(r'sample', views.SampleViewSet, base_name='sample')
# router.register(r'galaxy', views.GalaxyViewSet, base_name='galaxy')
# router.register(r'trait', views.TraitViewSet, base_name='trait')


object_nested_router = NestedExtendDefaultRouter(router, r'sample', lookup='sample')
object_nested_router.register(r'(?P<galaxy_pk>[^/.]+)', views.GalaxyViewSet, base_name='galaxy')

trait_nested_router = NestedExtendDefaultRouter(object_nested_router, r'(?P<galaxy_pk>[^/.]+)', lookup='galaxy')
trait_nested_router.register(r'(?P<trait_pk>[^/.]+)', views.TraitViewSet, base_name='trait')

traitprop_nested_router = NestedExtendDefaultRouter(trait_nested_router, r'(?P<trait_pk>[^/.]+)', lookup='trait')
traitprop_nested_router.register(r'(?P<traitproperty_pk>[^/.]+)', views.TraitPropertyViewSet, base_name='traitproperty')


urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='restapi_app/web_only/index.html'), name='index'),

    url(r'^data/', include(router.urls)),
    url(r'^data/', include(object_nested_router.urls)),
    url(r'^data/', include(trait_nested_router.urls)),
    url(r'^data/', include(traitprop_nested_router.urls)),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^relations/', include('django_spaghetti.urls')),
    url(r'^simple-get/$', views.CustomGet.as_view(), name='customget'),
    url(r'^model-free/resource/(?P<arg1>\w*\d*)[/]?(?P<arg2>\w*\d*)[/]?(?P<arg3>\w*\d*)[/]?', (views.ModelFreeView.as_view()), name='modelfree-list'),
    url(r'^model-free/resource/$', (views.ModelFreeView.as_view()), name='modelfree'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)

