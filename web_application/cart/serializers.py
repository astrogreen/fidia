import logging

from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse

from restapi_app.fields import AbsoluteURLField


class CartSerializer(serializers.Serializer):

    id = serializers.IntegerField(read_only=True)
    ao = serializers.CharField(max_length=256)
    url_list = serializers.JSONField()