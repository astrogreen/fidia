from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
import rest_framework.routers

import restapi_app.views
# import download.views

router = rest_framework.routers.SimpleRouter()


urlpatterns = [
    url(r'', include(router.urls)),

    url(r'download/$',
        restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='download/download.html'),
        name='download'),
    url(r'download/dummy-item/$',
        restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='download/dummy_item.html'),
        name='dummy-item'),
]


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
