from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.urlpatterns import format_suffix_patterns
import rest_framework.routers

import restapi_app.views
import download.views

router = rest_framework.routers.SimpleRouter()

# router.register(r'download-history', download.views.DownloadView, base_name='download')

urlpatterns = [
    url(r'', include(router.urls)),

    url(r'download/$',
        restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='download/download.html'),
        name='download'),
    url(r'download/dummy-item/$',
        restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='download/dummy_item.html'),
        name='dummy-item'),


    url(r'^download-create/$', download.views.DownloadCreateView.as_view(), name='download-create'),
    url(r'^download-history/$', download.views.DownloadListView.as_view(), name='download-list'),
    url(r'^download-history/(?P<pk>[0-9]+)/$', download.views.DownloadRetrieveDestroyView.as_view(), name='download-detail')
]

urlpatterns = format_suffix_patterns(urlpatterns)

# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
