from django.core.mail import send_mail

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


class ContactFormSerializer(serializers.Serializer):
    """
    Contact Form Serializer.
    """
    name = serializers.CharField(
        max_length=100,
        style={'placeholder':'Name'}
    )
    email = serializers.EmailField(
        max_length=100,
        style={'placeholder': 'Email'}
    )
    message = serializers.CharField(
        max_length=1000,
        style={'placeholder': 'Message', 'base_template': 'textarea.html', 'rows': 6}
    )

    def save(self):
        email = self.validated_data['email']
        message = self.validated_data['message']
        send_mail('Subject here', message=message, from_email=email, recipient_list=['liz.ophiuchus@gmail.com'],
                  fail_silently=False)
