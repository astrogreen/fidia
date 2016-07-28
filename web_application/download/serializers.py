import json
from rest_framework import serializers
import download.models


class DownloadSerializer(serializers.HyperlinkedModelSerializer):
    """
    Download Viewset serializer
    """
    def validate(self, data):
        try:
            json_object = json.loads(data['items'])
        except ValueError:
            raise serializers.ValidationError('Submitted data is not valid json')

    owner = serializers.ReadOnlyField(source='owner.username')
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    title = serializers.CharField(default='My Download', max_length=100)
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    items = serializers.JSONField(required=True, allow_null=False)
    downloadlink = serializers.URLField(required=False, max_length=150)

    class Meta:
        model = download.models.Download
        fields = ('title', 'items', 'owner', 'url', 'created', 'updated', 'downloadlink')
