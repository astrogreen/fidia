from django.conf.urls import url, include
import rest_framework.routers

import search.views

router = rest_framework.routers.SimpleRouter()
router.register(r'astro-objects', search.views.AstronomicalObjects, base_name='astro-object')

urlpatterns = [
    url(r'', include(router.urls)),
    url(r'^name-resolver/', search.views.NameResolver.as_view(), name='name-resolver'),
    url(r'^filter-by-name/', search.views.FilterByName.as_view(), name='filter-by-name'),
    url(r'^filter-by-id/', search.views.FilterById.as_view(), name='filter-by-id'),
    url(r'^filter-by-position/', search.views.FilterByPosition.as_view(), name='filter-by-position'),
]