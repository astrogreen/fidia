from __future__ import absolute_import, division, print_function, unicode_literals

# from typing import ...

# Python Standard Library Imports

# Other Library Imports

# FIDIA Imports
from .base_trait import Trait, TraitCollection
from .trait_property import TraitProperty

# Logging Import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

__all__ = ['Image', 'SpectralCube', 'DMU', 'WCS']

class WCS(Trait):
    pass

class Image(Trait):
    data = TraitProperty(dtype=(float, int), n_dim=2)
    exposed = TraitProperty(dtype=(float, int), optional=True)
    # wcs = SubTrait(WCS, optional=True)

class SpectralCube(Trait):
    data = TraitProperty(dtype=(float, int), n_dim=3)
    spatial_axes = (0, 1)
    wavelength_axis = 2

class DMU(TraitCollection):
    pass
