from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
import rest_framework.routers
import download.views


router = rest_framework.routers.SimpleRouter()
router.register(r'download', download.views.DownloadView, base_name='download-manager')
router.register(r'admin/download', download.views.AdminDownloadView, base_name='admin-download-manager')

urlpatterns = [
    url(r'', include(router.urls)),
    # url(r'^download-manager/$', download.views.DownloadView.as_view(), name='download-manager'),
    # url(r'^data-for/(?:(?P<object_type>[\w]+)/?)?$', sov.views.DataForType.as_view(), name='data-for'),


]