from rest_framework import serializers
from rest_framework.reverse import reverse


class AbsoluteURLField(serializers.Field):
    """
    Field for serializing url of endpoints for galaxy_pk
    """

    def __init__(self, **kwargs):
        self.url = kwargs.pop('url', '')
        super(AbsoluteURLField, self).__init__(**kwargs)

    def to_representation(self, obj):
        return self.url


