import logging
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

import feature.models

log = logging.getLogger(__name__)


class Vote(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = feature.models.Vote
        fields = ('url', 'id', "feature", "user")
        validators = [
            UniqueTogetherValidator(
                queryset=feature.models.Vote.objects.all(),
                fields=('user', 'feature'),
                message='User has already voted on feature'
            )
        ]


class VoteSlim(serializers.ModelSerializer):

    class Meta:
        model = feature.models.Vote
        fields = ('id',)


class Feature(serializers.ModelSerializer):
    feature_votes = VoteSlim(many=True, read_only=True)
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)

    class Meta:
        model = feature.models.Feature
        fields = ('url', 'id', "title", "description", "feature_votes", "created")


class FeatureUser(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)

    class Meta:
        model = feature.models.Feature
        fields = ('url', 'id', "title", "description", "user", "created")
