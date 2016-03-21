from rest_framework import serializers
from rest_framework.reverse import reverse


class AstroObjectAbsoluteURLField(serializers.Field):
    """
    Field for serializing url of endpoints for galaxy_pk
    """
    def to_representation(self, astro_object):
        url_kwargs = {
            'galaxy_pk': astro_object._identifier
        }
        return reverse("galaxy-list", kwargs=url_kwargs)


