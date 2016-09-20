from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import rest_framework.routers

import restapi_app.views


router = rest_framework.routers.SimpleRouter()

urlpatterns = [
            url(r'^$', restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/home/index.html'), name='index'),


            url(r'^surveys/$', restapi_app.views.Surveys.as_view(), name='surveys'),
            url(r'^tools/$', restapi_app.views.Tools.as_view(), name='tools'),


            url(r'^(?i)SAMI/$', restapi_app.views.SAMI.as_view(), name='sami'),
            url(r'^(?i)SAMI/data-products/$', restapi_app.views.SAMIDataProducts.as_view(), name='sami-data-products'),


            url(r'^(?i)GAMA/$', restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/documentation/underconstruction.html'), name='gama'),



            # url(r'^(?i)documentation/download/$', restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/documentation/download.html'),
            #                 name='documentation-download'),


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




            url(r'^(?i)under-construction/$',
                restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/documentation/underconstruction.html'),
                name='under-construction'),

            url(r'^(?i)about/team/$', restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='restapi_app/about/team.html'),
                name='about-team'),

            url(r'^(?i)support/contact/$', restapi_app.views.ContactForm.as_view(), name='support-contact'),




            # url(r'^user-testing/feedback/$',
            #   TemplateView.as_view(template_name='restapi_app/user-testing/feedback.html'),
            #   name='user-feedback'),
            # url(r'^user-testing/feature-tracking/$',
            #   TemplateView.as_view(template_name='restapi_app/user-testing/feature-tracking.html'),
            #   name='feature-tracking'),

            url(r'^(?i)data/catalogues/', restapi_app.views.AvailableTables.as_view(), name='catalogues'),


]


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
