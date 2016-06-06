from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static

from restapi_app.routers import ExtendDefaultRouter

import sov.views

router = ExtendDefaultRouter()

router.register(r'sov', sov.views.SOVListSurveysViewSet, base_name='sov')
router.register(r'sov', sov.views.SOVRetrieveObjectViewSet, base_name='sov')

urlpatterns = [
            url(r'', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
