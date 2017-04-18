from rest_framework import permissions, viewsets, mixins
import feature.models
import feature.serializers


class Feature(viewsets.ModelViewSet):
    """
    CRUD: Feature resource. Unauthenticated users are able to List and Retrieve.
    """
    serializer_class = feature.serializers.Feature
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None
    queryset = feature.models.Feature.objects.all()

    serializer_action_classes = {
        'list': feature.serializers.Feature,
        'retrieve': feature.serializers.Feature,
        'create': feature.serializers.FeatureUser,
        'update': feature.serializers.FeatureUser,
        'destroy': feature.serializers.FeatureUser,
    }

    def get_queryset(self):
        """
        Return a list of approved feature requests.
        """
        return feature.models.Feature.objects.filter(is_approved=True)

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super(Feature, self).get_serializer_class()


class Vote(mixins.CreateModelMixin,
           mixins.ListModelMixin,
           mixins.RetrieveModelMixin,
           mixins.DestroyModelMixin,
           viewsets.GenericViewSet):
    """
    Create, update and destroy votes belonging to authenticated user
    """
    serializer_class = feature.serializers.Vote
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """
        Return a list of all votes for the currently authenticated user.
        """
        user = self.request.user
        return feature.models.Vote.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Override CreateModelMixin perform_create to save object instance with ownership
        """
        serializer.save(user=self.request.user)


class VoteAdmin(viewsets.ModelViewSet):
    serializer_class = feature.serializers.Vote
    permission_classes = [permissions.IsAdminUser]
    pagination_class = None
    queryset = feature.models.Vote.objects.all()
