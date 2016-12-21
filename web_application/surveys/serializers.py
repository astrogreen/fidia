import logging
import json, os

from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse

from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar

import fidia, collections
from fidia.traits import Trait, TraitProperty
from fidia import traits
from fidia.descriptions import DescriptionsMixin

import sov.mixins


class RootSerializer(serializers.Serializer):
    """ Serializer for the Data Browser Root. Lists all surveys available from FIDIA. """

    def get_surveys(self, obj):
        return self.context['surveys']

    surveys = serializers.SerializerMethodField()



class SurveySerializer(sov.mixins.SurveyAttributesMixin):
    """ Serializer for the Data Browser Root. Lists survey's available astronomical objects. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        survey = self.instance
        assert isinstance(survey, fidia.Sample), \
            "SurveySerializer must have an instance of fidia.Sample, " + \
            "not '%s': try SurveySerializer(instance=sample)" % survey

        self.astro_objects = {}
        for astro_object in survey:
            url_kwargs = {
                'astroobject_pk': str(astro_object),
                'survey_pk': self.context['survey']
            }
            url = reverse("sov:astroobject-list", kwargs=url_kwargs)
            self.astro_objects[astro_object] = url

    def get_astro_objects(self, obj):
        return self.astro_objects

    astro_objects = serializers.SerializerMethodField()
