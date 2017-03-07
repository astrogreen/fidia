from django.contrib.auth.models import User
from rest_framework import serializers, status
from rest_framework_jwt.settings import api_settings

import restapi_app.exceptions


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password', 'confirm_password', 'token')

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

    token = serializers.SerializerMethodField()

    def get_token(self, obj):
        # Generate a JWT for newly-registered user
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(obj)
        return jwt_encode_handler(payload)

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
