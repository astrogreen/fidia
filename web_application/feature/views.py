from rest_framework import permissions, viewsets
import feature.models
import feature.serializers


class Feature(viewsets.ModelViewSet):
    """
    Create, update and destroy queries
    """
    serializer_class = feature.serializers.Feature
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    queryset = feature.models.Feature.objects.all()


class Vote(viewsets.ModelViewSet):
    """
    Create, update and destroy queries
    """
    serializer_class = feature.serializers.Vote
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    queryset = feature.models.Vote.objects.all()
