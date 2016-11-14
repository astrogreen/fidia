from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse


class SurveyAttributesMixin(serializers.Serializer):
    """ Mixin providing sample and data release info """

    survey = serializers.SerializerMethodField()
    data_release = serializers.SerializerMethodField()

    def get_survey(self, obj):
        return self.context['survey']

    def get_data_release(self, obj):
        return 1.0


class AstronomicalObjectAttributesMixin(SurveyAttributesMixin):
    """ Mixin providing current astroobject """

    astro_object = serializers.SerializerMethodField()

    def get_astro_object(self, obj):
        return self.context['astro_object']



