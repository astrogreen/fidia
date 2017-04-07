from django.conf.urls import url, include
import rest_framework.routers

import feature.views

router = rest_framework.routers.SimpleRouter()

router.register(r'feature', feature.views.Feature, base_name='feature')

urlpatterns = [
    url(r'', include(router.urls)),
]
