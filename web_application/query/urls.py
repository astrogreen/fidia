from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
import rest_framework.routers

import query.views

from restapi_app.routers import ExtendDefaultRouter, NestedExtendDefaultRouter
# router = ExtendDefaultRouter()

router = rest_framework.routers.SimpleRouter()

router.register(r'query-history', query.views.QueryListRetrieveUpdateDestroyView, base_name='query')
router.register(r'query', query.views.QueryCreateView, base_name='query-create')

urlpatterns = [
            url(r'', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
