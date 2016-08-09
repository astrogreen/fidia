from io import BytesIO
import logging

from rest_framework import renderers
from rest_framework.exceptions import UnsupportedMediaType
from fidia.traits import Trait

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class FITSRenderer(renderers.BaseRenderer):
    media_type = "application/fits"
    format = "fits"
    charset = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        log.debug("Render response: %s" % renderer_context['response'])
        trait = data.serializer.instance
        if not isinstance(trait, Trait):
            raise UnsupportedMediaType("Renderer doesn't support anything but Traits!")

        byte_file = BytesIO()

        trait.as_fits(byte_file)

        return byte_file.getvalue()


class ZipAORenderer(renderers.BaseRenderer):
    pass