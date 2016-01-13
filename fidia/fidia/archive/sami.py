from __future__ import absolute_import, division, print_function, unicode_literals

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)

log.enable_console_logging()

from glob import glob
import re
import os.path

from astropy.io import fits
import pandas as pd


# FIDIA Relative Imports
from .base_archive import BaseArchive
from ..galaxy import Galaxy

#from fidia.traits import
from ..sample import Sample
from ..traits.utilities import TraitKey, TraitMapping

# class dummy:
#     pass

class SAMITeamArchive(BaseArchive):

    def __init__(self, base_directory_path, master_catalog_path):
        super(SAMITeamArchive, self).__init__()
        self._base_directory_path = base_directory_path
        self._master_catalog_path = master_catalog_path
        self._contents = None
        self.available_traits = TraitMapping()
        self.define_available_traits()


    @property
    def contents(self):
        """List (set?) of available objects in this archive."""
        if self._contents is None:
            with fits.open(self._master_catalog_path) as m:
                # Master Catalogue is a binary table in extension 1 of the FITS File.
                self._contents = map(str, m[1].data['CATID'])
        return self._contents

    def data_available(self, object_id=None):
        if object_id is None:
            raise NotImplementedError("Don't know what data is available for the whole survey.")
        else:
            #self.validate_id(object_id)
            if object_id in self._cubes_available():
                print("Cubes available.")

    def can_provide(self, trait_key):
        # TODO: Implement!
        return True

    def _cubes_available(self):
        """Generate a list of objects which have "cubed" directories."""
        cube_ids = map(os.path.basename,glob(self._base_directory_path + "*/cubed/*"))

        # Note, there may be duplicates; the following prints a list of duplicates
        #print [item for item, count in collections.Counter(cube_ids).items() if count > 1]
        return cube_ids

    @property
    def name(self):
        return 'SAMI'

    def get_full_sample(self):
        """Return a sample containing all objects in the archive."""
        # Create an empty sample, and populate it via it's private interface
        # (no suitable public interface at this time.)
        new_sample = Sample()
        id_cross_match = pd.DataFrame(pd.Series(map(str, self.contents), name=self.name, index=self.contents))

        # For a new, empty sample, extend effectively just copies the id_cross_match into the sample's ID list.
        new_sample.extend(id_cross_match)

        # Add this archive to the set of archives associated with the sample.
        new_sample._archives = {self}

        # Finally, we mark this new sample as immutable.
        new_sample.mutable = False

        return new_sample

    def get_trait(self, object_id=None, trait_key=None):

        if trait_key is None:
            raise Exception("The TraitKey must be defined.")
        if not isinstance(trait_key, TraitKey) and isinstance(trait_key, tuple):
            trait_key = TraitKey(*trait_key)

        if object_id is not None:
            trait_key = trait_key._replace(object_id=object_id)

        # Determine which class responds to the requested trait. Potential for far more complex logic here in future.
        trait_class = self.available_traits[trait_key]

        # Create the trait object and return it.
        log.debug("Returning trait_class %s", type(trait_class))
        return trait_class(trait_key)

    def define_available_traits(archive):

        # Trait Definitions. These make up the "plugin"

        class SAMISpectralCube:

            @classmethod
            def data_available(cls, object_id):
                """Return a list of unique identifiers which can be used to retrieve actual data."""
                # Need to know the directory of the archive
                cube_files = glob(archive._base_directory_path + "*/cubed/" + object_id + "/*")
                return cube_files

            def __init__(self, key):
                self.object_id = key.object_id
                self.cube_file = key.trait_name
                if self.cube_file is None:
                    raise Exception("Must have trait_name to load data.")
                self.hdu = fits.open(self.cube_file)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.hdu.close()

            def name(self):
                pass

            def data(self):
                # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
                key = str('PRIMARY')
                return self.hdu[key].data

            def variance(self):
                # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
                return self.hdu[str('VARIANCE')].data

            def covariance(self):
                # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
                return self.hdu[str('COVAR')].data

            def weight(self):
                # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
                return self.hdu[str('WEIGHT')].data

        archive.available_traits[TraitKey('spectral_cubes', None, None)] = SAMISpectralCube

        return archive.available_traits
