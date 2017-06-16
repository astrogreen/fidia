from rest_framework import permissions, viewsets
import download.serializers, download.models


class DownloadView(viewsets.ModelViewSet):
    """
    Create, update and destroy downloads
    """
    serializer_class = download.serializers.DownloadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return a list of all downloads for the currently authenticated user.
        """
        user = self.request.user
        return download.models.Download.objects.filter(owner=user).order_by('-updated')

    def perform_create(self, serializer):
        """
        Override CreateModelMixin perform_create to save object instance with ownership
        """
        serializer.save(owner=self.request.user)
        # TODO detail route for e.g., data-download-limit


class AdminDownloadView(viewsets.ModelViewSet):
    serializer_class = download.serializers.AdminDownloadSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        """
        Return a list of all downloads for the currently authenticated user.
        """
        user = self.request.user
        return download.models.Download.objects.order_by('-updated')

    def perform_create(self, serializer):
        """
        Override CreateModelMixin perform_create to save object instance with ownership
        """
        serializer.save(owner=self.request.user)
