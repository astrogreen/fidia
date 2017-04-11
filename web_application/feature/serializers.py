import logging
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

import feature.models

log = logging.getLogger(__name__)


class Vote(serializers.ModelSerializer):
    vote_score = serializers.IntegerField(read_only=True)
    num_vote_up = serializers.BooleanField(default=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = feature.models.Vote
        fields = ('url', 'id', 'num_vote_up', "vote_score", "feature", "user")
        validators = [
            UniqueTogetherValidator(
                queryset=feature.models.Vote.objects.all(),
                fields=('user', 'feature'),
                message='User has already voted on feature'
            )
        ]


class VoteSlim(serializers.ModelSerializer):
    vote_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = feature.models.Vote
        fields = ('id', "vote_score")


class Feature(serializers.ModelSerializer):
    feature_votes = VoteSlim(many=True, read_only=True)

    class Meta:
        model = feature.models.Feature
        fields = ('url', 'id', "title", "description", "feature_votes",)
