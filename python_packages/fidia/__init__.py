
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
    from fidia.database_tools import Session


    # Set up the namespace
    import fidia.sample
    import fidia.traits
    import fidia.archive
    import fidia.column

    # from fidia.column import *
    # from fidia.sample import *
    from fidia.archive.archive import Archive, BasePathArchive


    from fidia.column.column_definitions import *
    from fidia.column.columns import FIDIAColumn, FIDIAArrayColumn

    # from fidia.traits.trait_key import TraitKey
    from fidia.traits import Trait, TraitCollection

    from .astro_object import AstronomicalObject

    from .sample import Sample


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

    # from fidia.database_tools import is_sane_database
    # if not is_sane_database(Session()):
    #     raise ImportError("FIDIA Database is invalid. Consider deleting the database.")