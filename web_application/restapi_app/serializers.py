from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from rest_framework import serializers, mixins, status


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
        max_length=100, label="Email (optional)**", required=False,
        style={'placeholder': 'Email'}
    )

    def send(self):
        subject, from_email, to = 'hello', 'from@example.com', 'liz.mannering@uwa.edu.au'
        text_content = 'This is an important message.'
        html_content = '<p>This is an <strong>important</strong> message.</p>'
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        #
        #
        # email = self.validated_data['email']
        # name = self.validated_data['name']
        #
        # message_to_send = "MESSAGE:" + self.validated_data['message'] + '<br>' + 'URL: ' +self.validated_data['url']
        #
        # send_mail('ADC Bug Report', message=message_to_send, from_email=email, recipient_list=['liz.mannering@uwa.edu.au'], fail_silently=False)
