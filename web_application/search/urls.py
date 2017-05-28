from django.conf.urls import url, include
import rest_framework.routers

import search.views

router = rest_framework.routers.SimpleRouter()
router.register(r'available-astro-objects', search.views.AstronomicalObjects, base_name='astro-object')

urlpatterns = [
    url(r'', include(router.urls)),
    url(r'^name-resolver/$', search.views.NameResolver.as_view(), name='name-resolver'),
    url(r'^filter-by/$', search.views.FilterBy.as_view(), name='filter'),
    url(r'^filter-by/(?:(?P<filter_term>[\w]+)/?)?$', search.views.FilterByTerm.as_view(), name='filter-by'),
]