from rest_framework import serializers


class SurveySerializer(serializers.Serializer):
    survey = serializers.SerializerMethodField()
    data_release = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()

    def get_survey(self, obj):
        return self.context['survey']

    def get_data_release(self, obj):
        return self.context['data_release']

    def get_count(self, obj):
        return self.context['count']
