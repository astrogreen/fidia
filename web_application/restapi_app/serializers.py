from time import gmtime, strftime

from django.utils.html import escape, format_html
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from rest_framework import serializers


"""
Serializers:

    Serializing and deserializing the query instances into json, csv representations.

A Serializer class is similar to a form class, and can include similar
validation flags such as required, max_length etc.

The field flags also control how the serializer should be displayed
e.g., when rendering to HTML. This is useful for controlling how the
browsable API should be displayed.



HyperlinkedModelSerializer sub-classes ModelSerializer and uses hyperlinked relationships
instead of primary key relationships.

"""


class SurveySerializer(serializers.Serializer):
    survey = serializers.SerializerMethodField()
    data_release = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()

    def get_survey(self, obj):
        return self.context['survey']

    def get_data_release(self, obj):
        return self.context['data_release']

    def get_count(self, obj):
        return self.context['count']


class DataProductSerializer(SurveySerializer):
    products = serializers.SerializerMethodField()

    def get_products(self, obj):
        return self.context['products']


class ContactFormSerializer(serializers.Serializer):
    """
    Contact Form Serializer.
    """
    name = serializers.CharField(
        max_length=100,
        style={'placeholder': 'Name'}
    )
    email = serializers.EmailField(
        max_length=100,
        style={'placeholder': 'Email'}
    )
    message = serializers.CharField(
        max_length=1000,
        style={'placeholder': 'Message', 'base_template': 'textarea.html', 'rows': 6}
    )

    def send(self):
        email = self.validated_data['email']
        message = self.validated_data['message']
        send_mail('ADC Contact Form', message=message, from_email=email, recipient_list=['liz.mannering@uwa.edu.au'],
                  fail_silently=False)


class BugReportSerializer(serializers.Serializer):
    """
    Contact Form Serializer.
    """
    message = serializers.CharField(
        max_length=10000, required=True, label="Message*",
        style={'placeholder': 'Please be as specific as possible when describing your issue.',
               'base_template': 'textarea.html', 'rows': 6}
    )
    url = serializers.CharField(required=False, label='URL (optional)', max_length=100,
                               style={'placeholder': 'e.g., /asvo/data-access/data-browser/'})

    name = serializers.CharField(
        max_length=100, required=True, label="Name*",
        style={'placeholder': 'Name'}
    )
    email = serializers.EmailField(
        max_length=100, label="Email*", required=True,
        style={'placeholder': 'Email'}
    )
    survey_team = serializers.ChoiceField(choices=['Not Applicable', 'GAMA', 'SAMI'], required=False,
                                          label='Survey Team (optional)', allow_blank=True)


    def send(self):

        from_email = str(self.validated_data.get('email'))
        survey_team = str(self.validated_data.get('survey_team'))
        message = str(self.validated_data.get('message'))
        url = str(self.validated_data.get('url'))
        name = str(self.validated_data.get('name'))
        date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

        snippet = """
        <h4>ADC Bug Report</h4>
            <table>
                <tr>
                    <td>External Reporter</td>
                    <td>{name}</td>
                </tr>
                <tr>
                    <td>Email</td>
                    <td>{from_email}</td>
                </tr>
                <tr>
                    <td>Survey Team</td>
                    <td>{survey_team}</td>
                </tr>
                <tr>
                    <td>Date</td>
                    <td>{date}</td>
                </tr>
                <tr>
                    <td>URL</td>
                    <td>{url}</td>
                </tr>
                <tr>
                    <td>Message</td>
                    <td>{message}</td>
                </tr>
            </table>
        """

        subject, from_email, to = 'ADC Bug Report', from_email, 'liz.mannering@uwa.edu.au'

        html_content = format_html(snippet, name=name, from_email=from_email, url=url, message=message, date=date,
                                   survey_team=survey_team)

        text_content = 'FROM: ' + name + ', ' + from_email + ', URL:' + url + ' MESSAGE: ' + message + ' DATE: ' + date
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
