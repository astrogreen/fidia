import logging
from django.contrib.auth.models import User
from django.utils.html import format_html
from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse

import restapi_app.exceptions


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    NOTE: many=True flag allows serialization of queryset instead of model instance.
    'query' is a reverse relationship on the User model, and will not be included by
    default in the (Hyperlinked)ModelSerializer class - so an explicit field is added.
    """
    query = serializers.HyperlinkedRelatedField(many=True, view_name='query-detail', read_only=True)

    class Meta:
        model = User
        fields = ('url', 'username', 'query', 'first_name', 'last_name', 'email',)
        extra_kwargs = {
            "username": {
                "read_only": True,
            },
        }


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    """
    User Profile serializer allows only first/last name & email to be updated
    """
    username = serializers.CharField(read_only=True)
    # query = serializers.HyperlinkedRelatedField(many=True, view_name='query-detail', read_only=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        extra_kwargs = {
            "username": {
                "read_only": True,
            },
        }

    def validate(self, data):
        """
        Checks username isn't being overwritten
        """
        if 'username' in data:
            # raise Conflict('Usernames cannot be changed')
            raise restapi_app.exceptions.CustomValidation
        return data
