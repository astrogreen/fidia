from __future__ import absolute_import, division, print_function, unicode_literals

# Python Standard Library Imports

# Other Library Imports

# FIDIA Imports
from .base_trait import Trait

# Set up logging
from fidia import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


class Image(Trait):

    display_name = "Image"

    # data = TraitPropertySlot(ndim=2)


class Spectrum(Trait):

    # data = TraitPropertySlot(ndim=1)
    pass
