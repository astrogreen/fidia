import logging
from rest_framework import serializers

import feature.models

log = logging.getLogger(__name__)


class FeatureSerializer(serializers.HyperlinkedModelSerializer):
    """

    """
    priority = serializers.IntegerField(read_only=True)

    class Meta:
        model = feature.models.Feature
        fields = ('url', 'id', "name", "description", "votes", "priority")
        # extra_kwargs = {'name': {'required': True}, "description": {"required": True},
        #                 "votes": {"required": False}, "priority": {"required": False}}
