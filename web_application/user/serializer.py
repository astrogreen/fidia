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

    username = serializers.CharField(read_only=True, label="Username")
    first_name = serializers.CharField(label="First Name")
    last_name = serializers.CharField(label="Last Name")
    email = serializers.EmailField(label="Email")
    date_joined = serializers.DateTimeField(read_only=True, format="%d/%m/%y %X", label="Date Joined")
    last_login = serializers.DateTimeField(read_only=True, format="%d/%m/%y %X", label="Last Login")
    query = serializers.HyperlinkedRelatedField(many=True, view_name='query-detail', read_only=True, label="Queries")
    can_update = serializers.SerializerMethodField()

    def get_can_update(self, obj):
        updatable = [
            {"name": "email", "pretty_name": "Email", "type": "email"},
            {"name": "first_name", "pretty_name": "First Name", "type": "text"},
            {"name": "last_name", "pretty_name": "Last Name", "type": "text"},
        ]
        # todo find a way to get the label dynamically
        # for f in self.Meta.fields:
        #     if f not in self.Meta.read_only_fields and f is not 'can_update':
        #         updatable.append({"name": f, "pretty_name": 'test'})
        return updatable

    class Meta:
        model = User
        fields = (
            'can_update',
            'username',
            'first_name',
            'last_name',
            'email',
            'query',
            'date_joined',
            'last_login',
            'groups',
            'is_superuser')
        read_only_fields = ('username', 'can_update', 'query', 'date_joined', 'last_login', 'groups', 'is_superuser')

    def validate(self, data):
        """
        Checks username isn't being overwritten
        """
        if 'username' in data:
            # raise Conflict('Usernames cannot be changed')
            raise restapi_app.exceptions.CustomValidation
        return data
