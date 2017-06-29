from rest_framework import serializers, mixins, status
import download.models


class DownloadSerializer(serializers.HyperlinkedModelSerializer):
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    title = serializers.CharField(required=True, max_length=100)

    class Meta:
        model = download.models.Download
        fields = ('title', 'data_list', 'created', 'updated', 'url', 'is_completed')
        extra_kwargs = {'url': {'view_name': 'download:download-manager-detail'}, "is_completed": {"read_only": True}}


class AdminDownloadSerializer(DownloadSerializer):
    # created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    # updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    owner = serializers.CharField(required=True, max_length=100)

    class Meta:
        model = download.models.Download
        fields = ('title', 'data_list', 'created', 'updated', 'url', 'is_completed', 'owner')
        extra_kwargs = {'url': {'view_name': 'download:download-manager-detail'}, "is_completed": {"read_only": True}}
