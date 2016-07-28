from rest_framework import serializers
import download.models


class DownloadSerializer(serializers.HyperlinkedModelSerializer):
    """
    Download Viewset serializer
    """
    owner = serializers.ReadOnlyField(source='owner.username')
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    title = serializers.CharField(default='My Download', max_length=100)
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    # items = serializers.JSONField(required=True, allow_null=False)

    class Meta:
        model = download.models.Download
        fields = ('title', 'items', 'owner', 'url', 'created', 'updated')