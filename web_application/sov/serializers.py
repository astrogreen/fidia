from rest_framework import serializers
from rest_framework.reverse import reverse

import fidia

from restapi_app.fields import AbsoluteURLField
from restapi_app.serializers import AstroObjectTraitSerializer


def get_and_update_depth_limit(kwargs):
    depth_limit = kwargs.pop('depth_limit', -1)
    if isinstance(depth_limit, int):
        if depth_limit > 0:
            depth_limit -= 1
        else:
            depth_limit = 0

    trait_pk = kwargs.pop('trait_pk', -1)
    if trait_pk == 'spectral_cube':
        depth_limit = 0
    return depth_limit


class SOVListSurveysSerializer(serializers.Serializer):
    """
    return list available objects in sample

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        sample = self.instance
        assert isinstance(sample, fidia.Sample), \
            "SampleSerializer must have an instance of fidia.Sample, " +\
            "not '%s': try SampleSerializer(instance=sample)" % sample

    # def get_url(self, view_name, astro_object):
        # url_kwargs = {
        #     'galaxy_pk': astro_object
        # }
        # return reverse(view_name, kwargs=url_kwargs)

    def get_name(self, obj_name):
        return obj_name

    def get_url(self, obj_name):
        url_kwargs = {
            'pk': obj_name
        }
        view_name = 'sov-detail'
        return reverse(view_name, kwargs=url_kwargs)

    name = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()


# class SOVRetrieveObjectSerializer(serializers.Serializer):
#     """
#     return object name & velocity map only
#
#     """
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         astro_object = self.instance
#         assert isinstance(astro_object, fidia.AstronomicalObject)
#         for trait in astro_object:
#             trait_key = trait
#             if str(trait_key) == "velocity_map" or 'line_map' in str(trait_key):
#                 self.fields[str(trait_key)] = \
#                     AstroObjectTraitSerializer(instance=astro_object[trait_key], depth_limit=2)
#
#     def get_samiID(self, obj):
#         return obj._identifier
#
#     def get_ra(self, obj):
#         return obj['spectral_cube-red'].ra()
#
#     def get_dec(self, obj):
#         return obj['spectral_cube-red'].dec()
#
#     samiID = serializers.SerializerMethodField()
#     ra = serializers.SerializerMethodField()
#     dec = serializers.SerializerMethodField()


class SOVRetrieveSerializer(serializers.Serializer):

    asvo_id = serializers.SerializerMethodField()
    ao_url = serializers.SerializerMethodField()
    # key_info = serializers.SerializerMethodField()

    def get_asvo_id(self,obj):
        return '0000001'

    def get_ao_url(self, instance):
        url_kwargs = {
            'galaxy_pk': instance._identifier
        }
        view_name = 'galaxy-list'
        return reverse(view_name, kwargs=url_kwargs)

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        astro_object = self.instance
        assert isinstance(astro_object, fidia.AstronomicalObject)


        def get_key_info(self, astro_object):
            pass

        for trait in astro_object:
            depth_limit = 0
            trait_key = trait

            url_kwargs = {
                'galaxy_pk': astro_object._identifier,
                'trait_pk': str(trait_key)
            }

            url = reverse("trait-list", kwargs=url_kwargs)
            if depth_limit == 0:
                self.fields[str(trait_key)] = AbsoluteURLField(url=url, required=False)
                # No details to be displayed below this level
            else:
                # Recurse displaying details at lower level
                self.fields[str(trait_key)] = \
                    AstroObjectTraitSerializer(instance=astro_object[trait_key], depth_limit=depth_limit)

    def get_schema(self, obj):
        return self.context['schema']

    schema = serializers.SerializerMethodField()
    # object = serializers.CharField(max_length=100, required=False, source="*")
