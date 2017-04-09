import logging
from rest_framework import serializers

import feature.models

log = logging.getLogger(__name__)


class Vote(serializers.ModelSerializer):
    vote_score = serializers.IntegerField(read_only=True)
    num_vote_up = serializers.BooleanField(default=True)

    class Meta:
        model = feature.models.Vote
        fields = ('url', 'id', 'num_vote_up', "vote_score", "feature", "user")


class Feature(serializers.ModelSerializer):
    """

    """
    votes = Vote(many=True, read_only=True)

    class Meta:
        model = feature.models.Feature
        fields = ('url', 'id', "title", "description", "votes", )
