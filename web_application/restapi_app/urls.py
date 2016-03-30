from django.conf.urls import url, include
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import SimpleRouter

from django.views.generic import TemplateView
from .routers import ExtendDefaultRouter, NestedExtendDefaultRouter
from django.conf import settings
from django.conf.urls.static import static

router = ExtendDefaultRouter()

router.register(r'query', views.QueryViewSet)
# router.register(r'users', views.UserViewSet)
router.register(r'browse', views.SOVListSurveysViewSet, base_name='browse')
router.register(r'browse', views.SOVRetrieveObjectViewSet, base_name='browse')
router.register(r'sample', views.SampleViewSet, base_name='sample')

# Nested routes for sample
object_nested_router = NestedExtendDefaultRouter(router, r'sample', lookup='sample')
object_nested_router.register(r'(?P<galaxy_pk>[^/.]+)', views.AstroObjectViewSet, base_name='galaxy')

trait_nested_router = NestedExtendDefaultRouter(object_nested_router, r'(?P<galaxy_pk>[^/.]+)', lookup='galaxy')
trait_nested_router.register(r'(?P<trait_pk>[^/.]+)', views.TraitViewSet, base_name='trait')

traitprop_nested_router = NestedExtendDefaultRouter(trait_nested_router, r'(?P<trait_pk>[^/.]+)', lookup='trait')
traitprop_nested_router.register(r'(?P<traitproperty_pk>[^/.]+)', views.TraitPropertyViewSet, base_name='traitproperty')

# keep users out of the api-root router.register
user_list = views.UserViewSet.as_view({
    'get': 'list'
})
user_detail = views.UserViewSet.as_view({
    'get': 'retrieve'
})

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='restapi_app/home/index.html'), name='index'),
    url(r'^documentation/$', TemplateView.as_view(template_name='restapi_app/documentation/documentation.html'), name='documentation'),
    url(r'^logged-out/$', TemplateView.as_view(template_name='restapi_app/user/logout.html'), name='logout-page'),

    url(r'^data/', include(router.urls)),
    url(r'^data/', include(object_nested_router.urls)),
    url(r'^data/', include(trait_nested_router.urls)),
    url(r'^data/', include(traitprop_nested_router.urls)),

    url(r'^data/catalogues/', views.AvailableTables.as_view(), name='catalogues'),

    url(r'^users/$', user_list, name='user-list'),
    url(r'^users/(?P<pk>[0-9]+)/$', user_detail, name='user-detail'),

    url(r'^register/', views.CreateUserView.as_view(), name='user-register'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)

