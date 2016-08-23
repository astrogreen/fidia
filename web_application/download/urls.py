from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.urlpatterns import format_suffix_patterns
import rest_framework.routers

import restapi_app.views
import download.views

router = rest_framework.routers.SimpleRouter()

# router.register(r'storage', download.views.StorageViewSet, base_name='storage')

urlpatterns = [
    url(r'', include(router.urls)),

    url(r'^session/$', download.views.SessionView.as_view(), name='session-list'),

    url(r'^download/$', download.views.DownloadCreateView.as_view(), name='download-create'),
    url(r'^download-history/$', download.views.DownloadListView.as_view(), name='download-list'),
    url(r'^download-history/(?P<pk>[0-9]+)/$', download.views.DownloadRetrieveDestroyView.as_view(), name='download-detail')
]

urlpatterns = format_suffix_patterns(urlpatterns)

# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
