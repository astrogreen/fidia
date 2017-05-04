from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
import rest_framework.routers

import query.views

router = rest_framework.routers.SimpleRouter()

router.register(r'query', query.views.Query, base_name='query')

# router.register(r'result', query.views.Result, base_name='result')

urlpatterns = [
    url(r'^query-schema/$', query.views.QuerySchema.as_view(), name='query-schema'),
    url(r'', include(router.urls)),
]