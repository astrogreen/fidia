from django.conf.urls import url, include
from . import views

from restapi_app.routers import ExtendDefaultRouter, NestedExtendDefaultRouter
from django.conf import settings
from django.conf.urls.static import static

router = ExtendDefaultRouter()


router.register(r'query-history', views.QueryListRetrieveUpdateDestroyView, base_name='query')
router.register(r'query', views.QueryCreateView, base_name='query-create')


urlpatterns = [
            url(r'', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
