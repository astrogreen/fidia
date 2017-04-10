"""The DYNAMO FIDIA Archive Interface"""

# Set Up Logging
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)

log.enable_console_logging()

from glob import glob
import re
import os.path

from astropy.io import fits

from fidia.base_classes import BaseArchive
from ..galaxy import Galaxy



class DynamoArchive(BaseArchive):

    _dynamo_name_re = re.compile("""
            (EL|L|M|H|SH)
            (flux|lum)
            (L|H|A)z
            _
            (\d{1,2})
            -
            (\d+)
        """,
       flags=re.VERBOSE)

    @classmethod
    def is_dynamo_name(cls, name):
        if cls._dynamo_name_re.match(name):
            return True
        else:
            return False

    def __init__(self, base_directory):
        super(DynamoArchive, self).__init__()

        self._base_directory = os.path.abspath(base_directory)

        contents = []

        # Check the contents of the directory, and add any galaxies found
        dir_contents = glob(os.path.join(self._base_directory, "*"))
        for item in dir_contents:
            # Extract just the name
            item_name = os.path.basename(item)
            if DynamoArchive.is_dynamo_name(item_name) and os.path.isdir(item):
                # The name is a valid DYNAMO object
                contents.append(item_name)
        self._contents = set(contents)

    @property
    def contents(self):
        return self._contents



    def object_template(self, id):

        # Iterate through all necessary steps to create complete galaxy with
        # all of the available stuff attached? Seems kind of complicated and
        # inefficient.
        #
        # What if we could instead define a "factory" in a seperate file,
        # where instructions for how to load each of the parts are defined. We
        # could then just return the pointer to that factory, which would in
        # turn construct and cache the relevant stuff as needed.
#        gal.add_map()

        class gal(object):

            #@fidia.types.map
            def ha_velocity():
                with fits.open(self.map_data_path(self.galaxy_id, 'velmap')) as f:
                    m = fidia.data_types.RegularMap(f[0].data)
                    m.coordinates = None
                    m.units = None

                return m

            def coordinates():
                return (23, 45)


        return gal



    def available_maps(self, galaxy_id):
        self.validate_galaxy_id(galaxy_id)
        dir_contents = glob(self.maps_directory(galaxy_id) + "/*")
        available_maps = []
        for item in dir_contents:
            item_name = os.path.basename(item)
            log.debug("Considering item_name: %s", item_name)
            match = re.match("fs" + galaxy_id + "_([^\\.]+).fits",
                item_name)
            if match is not None:
                available_maps.append(match.group(1))
        return available_maps

    def maps_directory(self, galaxy_id):
        mapsdir = os.path.join(
            self._base_directory,
            galaxy_id, 
            "fs" + galaxy_id + "_maps")
        log.debug("Maps directory is: %s", mapsdir)

        return mapsdir

    def map_data_path(self, galaxy_id, map_type):
        path = os.path.join(
             self._base_directory,
             galaxy_id, 
            "fs" + galaxy_id + "_maps",
            "fs" + galaxy_id + "_" + map_type + ".fits")
        log.debug("Path: %s", path)
        if os.path.isfile(path):
            return path
        else:
            raise Exception("Requested map '{}' not found for galaxy '{}'".format(
                map_type, galaxy_id))

    def validate_galaxy_id(self, galaxy_id):
        """Throw an exception if the galaxy is not valid for this archive."""
        if galaxy_id not in self._contents:
            raise Exception("Galaxy '{}' not found.".format(galaxy_id))
    







