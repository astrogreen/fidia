# Copyright (c) Australian Astronomical Observatory (AAO), 2018.
#
# The Format Independent Data Interface for Astronomy (FIDIA), including this
# file, is free software: you can redistribute it and/or modify it under the terms
# of the GNU Affero General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.


# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *
# ----------------------------------------------------------------------------

# For egg_info test builds to pass, put package imports here.
if not _ASTROPY_SETUP_:

    pass


    # Set up global application state first:

    #     Load configuration information (from fidia.ini files if found), and
    #     make it available:
    from fidia.local_config import config

    #     Connect to the persistence database as defined by the config
    #     information (or use the default in-memory persistance database). Then
    #     get the database Session factory to be used for this instance of
    #     FIDIA.
    from fidia.database_tools import mappingdb_session


    # Set up the namespace
    import fidia.sample
    import fidia.traits
    import fidia.archive
    import fidia.column
    import fidia.dal

    # from fidia.column import *
    # from fidia.sample import *
    from fidia.archive.archive import Archive, BasePathArchive, DatabaseArchive


    from fidia.column.column_definitions import *
    from fidia.column.columns import FIDIAColumn, FIDIAArrayColumn

    # from fidia.traits.trait_key import TraitKey
    from fidia.traits import Trait, TraitCollection

    from .astro_object import AstronomicalObject

    from .sample import Sample

    from .archive.archive import ArchiveDefinition


    # from .sample import Sample
    # from .astro_object import AstronomicalObject
    #
    # from .column import *
    #
    # from .exceptions import *
    #
    # from .descriptions import *

    # from .archive import *

    # Ensure the database is in a sensible state

    from fidia.database_tools import check_create_update_database
    check_create_update_database()

    # Create various singleton instances:
    known_archives = fidia.archive.archive.KnownArchives()
    dal_host = fidia.dal.DataAccessLayerHost(config)

    # from fidia.database_tools import is_sane_database
    # if not is_sane_database(Session()):
    #     raise ImportError("FIDIA Database is invalid. Consider deleting the database.")

    from fidia.archive.example_archive import ExampleArchive