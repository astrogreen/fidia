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

__all__ = ['Image', 'SpectralCube', 'DMU', 'ImageWCS']

class ImageWCS(Trait):
    n_axis = 2
    crpix1 = TraitProperty(dtype=(float, int))
    crpix2 = TraitProperty(dtype=(float, int))
    crval1 = TraitProperty(dtype=(float, int))
    crval2 = TraitProperty(dtype=(float, int))
    cdelt1 = TraitProperty(dtype=(float, int))
    cdelt2 = TraitProperty(dtype=(float, int))
    ctype1 = TraitProperty(dtype=str)
    ctype2 = TraitProperty(dtype=str)



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
