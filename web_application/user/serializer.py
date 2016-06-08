import logging
from django.contrib.auth.models import User

from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse

from restapi_app.exceptions import Conflict, CustomValidation
import user.models


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password', 'confirm_password')

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    email = serializers.EmailField(
        allow_blank=False, required=True
    )
    username = serializers.CharField(required=True, allow_blank=False)
    password = serializers.CharField(
        write_only=True, required=True, allow_blank=False,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        allow_blank=False, write_only=True,
        required=True, style={'input_type': 'password'}
    )

    def validate(self, data):
        """
        Checks to be sure that the received password and confirm_password
        fields are exactly the same
        """
        if User.objects.filter(username=data['username']).exists():
            raise Conflict('User %s already exists' % data['username'])

        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError("Passwords do not match")

        return data

    def create(self, validated_data):
        user = super(CreateUserSerializer, self).create(validated_data)
        if 'password' in validated_data:
            user.set_password(validated_data['password'])
            user.save()
        return user


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


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    """
    NOTE: many=True flag allows serialization of queryset instead of model instance.
    'query' is a reverse relationship on the User model, and will not be included by
    default in the (Hyperlinked)ModelSerializer class - so an explicit field is added.
    """

    class Meta:
        model = User
        fields = ('url', 'username', 'first_name', 'last_name', 'email',)

