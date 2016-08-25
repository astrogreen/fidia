from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import rest_framework.routers

import restapi_app.views
import documentation.views

router = rest_framework.routers.SimpleRouter()

router.register(r'documentation/SAMI', documentation.views.SAMIDocumentation, base_name="sami-docs")

urlpatterns = [
            url(r'documentation/$',
                restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='documentation/root.html'),
                name='root'),

            url(r'', include(router.urls)),

            #
            # url(r'^(?i)documenation/syntax/$', restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/documentation/syntax.html'),
            #                 name='documentation-syntax'),
            # url(r'^(?i)documentation/download/$', restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/documentation/download.html'),
            #                 name='documentation-download'),
            #
            #
            # url(r'^(?i)documentation/data-access/$',
            #     restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/documentation/data-access.html'),
            #     name='documentation-data-access'),
            # url(r'^(?i)documentation/query-builder/$',
            #     restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/documentation/query-builder.html'),
            #     name='documentation-query-builder'),
            # url(r'^(?i)documentation/query-history/$',
            #     restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/documentation/query-history.html'),
            #     name='documentation-query-history'),
            # url(r'^(?i)documentation/schema-browser/$',
            #     restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/documentation/schema-browser.html'),
            #     name='documentation-schema-browser'),
            #
            #
            # url(r'^(?i)faq/$', restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/faq/root.html'),
            #                 name='faq'),
            # url(r'^(?i)faq/data-browser/$', restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/faq/data-browser.html'),
            #                 name='faq-data-browser'),
            # url(r'^(?i)faq/query/$', restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/faq/query.html'),
            #                 name='faq-query'),
            #
            #



]