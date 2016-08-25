from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import rest_framework.routers

import restapi_app.views
import documentation.views

router = rest_framework.routers.SimpleRouter()

router.register(r'documentation/(?i)sami', documentation.views.SAMIDocumentation, base_name="sami-docs")

urlpatterns = [
    url(r'documentation/$',
        restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='documentation/root.html'),
        name='root'),

    url(r'', include(router.urls)),

]
