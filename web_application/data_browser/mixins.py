from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse


class SampleAttributesMixin(serializers.Serializer):
    """ Mixin providing sample and data release info """

    sample = serializers.SerializerMethodField()
    data_release = serializers.SerializerMethodField()

    def get_sample(self, obj):
        return self.context['sample']

    def get_data_release(self, obj):
        return 1.0


class AstronomicalObjectAttributesMixin(SampleAttributesMixin):
    """ Mixin providing current astroobject """

    astro_object = serializers.SerializerMethodField()

    def get_astro_object(self, obj):
        return self.context['astro_object']



