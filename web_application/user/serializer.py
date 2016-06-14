import logging
from django.contrib.auth.models import User
from django.utils.html import format_html
from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse

import restapi_app.exceptions


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password', 'confirm_password')

    first_name = serializers.CharField(required=True, allow_blank=False)
    last_name = serializers.CharField(required=True, allow_blank=False)

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
        fields are exactly the same (but confirm_password isn't saved anywhere)
        """
        if User.objects.filter(username=data['username']).exists():
            raise restapi_app.exceptions.Conflict('User %s already exists' % data['username'])

        if User.objects.filter(email=data['email']).exists():
            message = 'Email %s already registered.' % data['email']
            raise restapi_app.exceptions.Conflict(message)

        if data['password'] != data.pop('confirm_password'):
            # raise serializers.ValidationError("Passwords do not match")
            raise restapi_app.exceptions.CustomValidation(detail='Passwords do not match', field='detail', status_code=status.HTTP_400_BAD_REQUEST)

        if len(data['username']) > 50:
            message = 'User %s too long. Please limit to 50 characters' % data['username']
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_400_BAD_REQUEST)
        return data

    def create(self, validated_data):
        user = super(CreateUserSerializer, self).create(validated_data)
        if 'password' in validated_data:
            user.set_password(validated_data['password'])
            user.is_staff = False
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
    query = serializers.HyperlinkedRelatedField(many=True, view_name='query-detail', read_only=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'query')
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


# class UserPasswordSerializer(serializers.HyperlinkedModelSerializer):
#     """
#     NOTE: many=True flag allows serialization of queryset instead of model instance.
#     'query' is a reverse relationship on the User model, and will not be included by
#     default in the (Hyperlinked)ModelSerializer class - so an explicit field is added.
#     """
#     username = serializers.CharField(read_only=True)
#
#     class Meta:
#         model = User
#         fields = ('username', 'password')


# class UserPasswordChangeSerializer(serializers.Serializer):
#     email = serializers.EmailField(
#         allow_blank=False, required=True
#     )
#     username = serializers.CharField(required=True, allow_blank=False)
#     password = serializers.CharField(
#         write_only=True, required=True, allow_blank=False,
#         style={'input_type': 'password'}
#     )
#
#     class Meta:
#         fields = ('username', 'password', 'email',)
#
#     def update(self, instance, validated_data):
#         instance.password = validated_data.get('password', instance.password)
#         return instance
#
#
# class ChangePasswordSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = User
#         field = ('username', 'email')