from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
import rest_framework.routers

import query.views

router = rest_framework.routers.SimpleRouter()

# router.register(r'query-history', query.views.QueryListRetrieveUpdateDestroyView, base_name='query')
# router.register(r'data-access/query', query.views.QueryCreateView, base_name='query-create')
router.register(r'query', query.views.Query, base_name='query')
# router.register(r'query-schema', query.views.QuerySchema, base_name='query-schema')

urlpatterns = [
    url(r'^query-schema/$', query.views.QuerySchema.as_view(), name='query-schema'),
    url(r'', include(router.urls)),
]
