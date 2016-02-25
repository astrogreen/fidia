from io import BytesIO

from rest_framework import renderers
from rest_framework.exceptions import UnsupportedMediaType

from fidia.traits.base_traits import Trait

class FITSRenderer(renderers.BaseRenderer):
    media_type = "application/fits"
    format = "fits"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        trait = data.serializer.instance
        if not isinstance(trait, Trait):
            raise UnsupportedMediaType("Renderer doesn't support anything but Traits!")

        byte_file = BytesIO()

        trait.as_fits(byte_file)

        return byte_file.getvalue()