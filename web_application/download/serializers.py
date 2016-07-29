from django.db.models import Sum
import json
from rest_framework import serializers

import download.models


class DownloadCreateSerializer(serializers.HyperlinkedModelSerializer):
    """
    Download Viewset serializer
    """
    def validate_downloaditems(self, data):
        try:
            json_object = json.loads(data)
        except ValueError:
            raise serializers.ValidationError('Submitted data is not valid json')
        return data

    owner = serializers.ReadOnlyField(source='owner.username')
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    title = serializers.CharField(default='My Download', max_length=100)
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    downloaditems = serializers.JSONField(required=True, allow_null=False)
    downloadlink = serializers.URLField(required=False, max_length=150, read_only=True)

    class Meta:
        model = download.models.Download
        fields = ('title', 'downloaditems', 'owner', 'url', 'created', 'updated', 'downloadlink')


class DownloadSerializer(serializers.HyperlinkedModelSerializer):
    """
    Download List serializer
    """
    owner = serializers.ReadOnlyField(source='owner.username')
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    title = serializers.CharField(default='My Download', max_length=100)
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    downloaditems = serializers.JSONField(required=True, allow_null=False)
    downloadlink = serializers.URLField(max_length=150, read_only=True)
    total_size = serializers.SerializerMethodField()

    def get_total_size(self, obj):
        return download.models.Download.objects.aggregate(Sum('size'))

    class Meta:
        model = download.models.Download
        fields = ('title', 'downloaditems', 'owner', 'url', 'created', 'updated', 'downloadlink', 'size', 'total_size')
