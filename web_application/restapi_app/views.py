import json, requests
from django.views.generic import TemplateView
from django.conf import settings
from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response
from rest_framework.settings import api_settings
from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar
import restapi_app.exceptions
import restapi_app.serializers
import restapi_app.renderers
import restapi_app.permissions
import data_browser.serializers

AVAILABLE_SURVEYS = ["sami", "gama"]


class TemplateViewWithStatusCode(TemplateView):
    """
    Adds a status code to the mix. api.html (which all templates extend)
    looks for a status code to determine content or status rendering
    (albeit lazily, if one isn't found it sets to HTTP_200_OK).
    """

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context, status=status.HTTP_200_OK)


class AvailableTables(views.APIView):
    def get(self, request, format=None):
        """
        Return hardcoded response: json data of available tables
        """
        with open('restapi_app/gama_database.json') as json_d:
            json_data = json.load(json_d)
        return Response(json_data)


# class ContactForm(views.APIView):
#     """
#     Contact Form
#     """
#
#     permission_classes = (permissions.AllowAny,)
#     renderer_classes = [renderers.TemplateHTMLRenderer]
#     template_name = 'restapi_app/support/contact.html'
#
#     def get(self, request):
#         serializer = restapi_app.serializers.ContactFormSerializer
#
#         return Response(data={'serializer': serializer, 'email_status': 'unbound'}, status=status.HTTP_200_OK)
#
#     def post(self, request, format=None):
#         serializer = restapi_app.serializers.ContactFormSerializer(data=request.data)
#         serializer.is_valid()
#
#         if serializer.is_valid():
#             serializer.send()
#             serializer_unbound = restapi_app.serializers.ContactFormSerializer
#             return Response({"email_status": "success", 'serializer': serializer_unbound},
#                             status=status.HTTP_202_ACCEPTED)
#
#         return Response({"email_status": "error"}, status=status.HTTP_400_BAD_REQUEST)




def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def validateRecaptcha(self, request):
    # Validate the recaptcha box

    # Get user's response
    captcha_rs = request.POST.get('g-recaptcha-response')

    url = "https://www.google.com/recaptcha/api/siteverify"
    params = {
        'secret': '6LdTGw8TAAAAACaJN7aHD44SVDccIWE-ssIzEQ4j',
        'response': captcha_rs,
        'remoteip': get_client_ip(request)
    }

    response_content = requests.post(url, data=params)
    verify_rs = response_content.json()

    recaptcha = {}
    recaptcha["status"] = verify_rs.get("success", False)
    recaptcha['message'] = verify_rs.get('error-codes', None) or "Unspecified error."
    return recaptcha


class ContactForm(views.APIView):
    """
    Contact Form
    """
    permission_classes = (permissions.AllowAny,)
    renderer_classes = [renderers.TemplateHTMLRenderer]
    template_name = 'restapi_app/support/contact.html'

    def get(self, request):
        print(request.META['HTTP_HOST'])
        serializer = restapi_app.serializers.ContactFormSerializer
        return Response(data={'serializer': serializer, 'display_form': True}, status=status.HTTP_200_OK)

    def post(self, request, format=None):

        serializer_unbound = restapi_app.serializers.ContactFormSerializer

        try:
            # access request data
            serializer = restapi_app.serializers.ContactFormSerializer(data=request.data)
        except BaseException as e:
            return Response({"email_status": "server_error",
                             "message": 'Server Error (' + str(e) + ').',
                             'serializer': serializer_unbound, 'data': request.data,
                             'display_form': True},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer.is_valid()

        if serializer.is_valid():

            recaptcha = validateRecaptcha(self, request)
            print(recaptcha['status'])

            if recaptcha['status'] is True:
                try:
                    serializer.send()
                    return Response({"email_status": "success", 'display_form': False}, status=status.HTTP_202_ACCEPTED)
                except BaseException as e:
                    return Response({"email_status": "server_error",
                                     "message": 'Server Error (' + str(
                                         e) + '): Contact form could not be sent at this time.',
                                     'serializer': serializer, 'display_form': True},
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    {"email_status": "client_error", "message": "Recaptcha Failed. Are you a robot?",
                     'serializer': serializer,
                     'display_form': True},
                    status=status.HTTP_400_BAD_REQUEST)

        else:
            #  Client Error: serializer is not valid. Return errors and bound form
            return Response(
                {"email_status": "client_error", "errors": json.dumps(serializer.errors), 'serializer': serializer,
                 'display_form': True},
                status=status.HTTP_400_BAD_REQUEST)


class BugReport(views.APIView):
    """
    Bug Report Form
    """

    permission_classes = (permissions.AllowAny,)
    renderer_classes = [renderers.TemplateHTMLRenderer]
    template_name = 'restapi_app/support/bug_report.html'

    def get(self, request):
        serializer = restapi_app.serializers.BugReportSerializer
        return Response(data={'serializer': serializer, 'display_form': True}, status=status.HTTP_200_OK)

    def post(self, request, format=None):

        serializer_unbound = restapi_app.serializers.BugReportSerializer

        try:
            # access request data
            serializer = restapi_app.serializers.BugReportSerializer(data=request.data)
        except BaseException as e:
            return Response({"email_status": "server_error",
                             "message": 'Server Error (' + str(e) + ').',
                             'serializer': serializer_unbound, 'data': request.data,
                             'display_form': True},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer.is_valid()

        if serializer.is_valid():

            try:
                serializer.send()
                return Response({"email_status": "success", 'display_form': False}, status=status.HTTP_202_ACCEPTED)
            except BaseException as e:
                return Response({"email_status": "server_error",
                                 "message": 'Server Error (' + str(e) + '): Bug report could not be sent at this time.',
                                 'serializer': serializer, 'display_form': True},
                                status=status.HTTP_400_BAD_REQUEST)

        else:
            #  Client Error: serializer is not valid. Return errors and bound form
            return Response(
                {"email_status": "client_error", "errors": json.dumps(serializer.errors), 'serializer': serializer,
                 'display_form': True},
                status=status.HTTP_400_BAD_REQUEST)


class Surveys(views.APIView):
    """
    Available Surveys page
    """
    permission_classes = (permissions.AllowAny,)

    class SurveyRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'restapi_app/surveys/overview.html'

    renderer_classes = (SurveyRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def get(self, request):
        surveys = [{"survey": "sami", "count": sami_dr1_sample.ids.__len__(), "current_version": 1.0,
                    'data_releases': [1.0, ]}]

        serializer_class = data_browser.serializers.RootSerializer
        _dummy = object
        serializer = serializer_class(
            many=False, instance=_dummy,
            context={'request': request, 'surveys': surveys},
        )

        return Response(serializer.data)


class SAMI(views.APIView):
    """
    Available Surveys page
    """
    permission_classes = (permissions.AllowAny,)

    class SurveyRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'restapi_app/surveys/sami/home.html'

    renderer_classes = (SurveyRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def get(self, request):
        self.breadcrumb_list = ['SAMI']

        serializer_class = restapi_app.serializers.SurveySerializer
        _dummy = object
        serializer = serializer_class(
            many=False, instance=_dummy,
            context={'request': request,
                     "survey": "sami",
                     "count": sami_dr1_sample.ids.__len__(),
                     "data_release": 1.0},
        )

        return Response(serializer.data)


# TODO surveys as resources list.



class SAMIDataProducts(views.APIView):
    """
    Available Surveys page
    """
    permission_classes = (permissions.AllowAny,)

    class SurveyRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        pass
        template = 'restapi_app/surveys/sami/data-products.html'

    renderer_classes = (SurveyRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def get(self, request):
        self.breadcrumb_list = ['SAMI', 'Data Products']

        serializer_class = restapi_app.serializers.DataProductSerializer
        _dummy = object
        serializer = serializer_class(
            many=False, instance=_dummy,
            context={'request': request,
                     "survey": "sami",
                     "count": sami_dr1_sample.ids.__len__(),
                     "data_release": 1.0,
                     "products": {
                         "product1": {
                             "description": None,
                             "pretty_name": "Product 1", },
                         "product2": {
                             "description": None,
                             "pretty_name": "Product 2", }
                     },
                     }
        )

        return Response(serializer.data)


class DataAccess(views.APIView):
    """
    Available Surveys page
    """
    permission_classes = (permissions.AllowAny,)

    class ToolRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'restapi_app/data-access/overview.html'

    renderer_classes = (ToolRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def get(self, request):
        surveys = [{"survey": "sami", "count": sami_dr1_sample.ids.__len__(), "current_version": 1.0,
                    'data_releases': [1.0, ]}]

        serializer_class = data_browser.serializers.RootSerializer
        _dummy = object
        serializer = serializer_class(
            many=False, instance=_dummy,
            context={'request': request, 'surveys': surveys},
        )

        return Response(serializer.data)
