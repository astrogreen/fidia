from __future__ import absolute_import, division, print_function, unicode_literals

# from typing import List
import fidia

# Python Standard Library Imports

# Other Library Imports

# FIDIA Imports
import fidia.base_classes as bases
# from fidia.utilities import snake_case
# from .traits import TraitKey

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.VDEBUG)
log.enable_console_logging()

__all__ = ['AstronomicalObject']


class AstronomicalObject(object):

    def __init__(self, sample, identifier=None, ra=None, dec=None):
        # type: (fidia.Sample, str, float, float) -> None
        if identifier is None:
            if ra is None or dec is None:
                raise Exception("Either 'identifier' or 'ra' and 'dec' must be defined.")
            self._identifier = "J{ra:3.6}{dec:+2.4d}".format(ra=ra, dec=dec)
        else:
            self._identifier = identifier

        # Reference to the sample containing this object.
        self.sample = sample

        # Dictionary of IDs for this object in the various archives attached
        # to the sample. @TODO: Initialised to None: must be populated
        # separately.
        # self._archive_id = {archive: None for archive in sample.archives}

        self._ra = ra
        self._dec = dec

        # Associate TraitPointer objects as necessary.

        self.update_trait_pointers()

        super(AstronomicalObject, self).__init__()

    @property
    def identifier(self):
        return self._identifier

    @property
    def ra(self):
        return self._ra

    @property
    def dec(self):
        return self._dec

    def update_trait_pointers(self):

        from fidia.traits.trait_utilities import TraitPointer

        # Clear all existing pointers to TraitPointers
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, bases.TraitPointer):
                delattr(self, attr_name)
        log.debug("Creating Trait Pointers for AstroObject %s", self)
        if log.isEnabledFor(slogging.VDEBUG):
            message = str(self.sample.trait_mappings.as_nested_dict())
            log.vdebug("TraitMappings available: %s", message)
        for trait_type in self.sample.trait_mappings.keys(1):
            # pointer_name = snake_case(trait_mapping.trait_class.trait_class_name())
            log.debug("Adding TraitPointer '%s'", trait_type)
            setattr(self, trait_type, TraitPointer(trait_type, self.sample, self, None))

    def get_archive_id(self, archive):
        return self.sample.get_archive_id(archive, self._identifier)
