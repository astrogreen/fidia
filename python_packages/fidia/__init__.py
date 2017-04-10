
# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *
# ----------------------------------------------------------------------------

# For egg_info test builds to pass, put package imports here.
if not _ASTROPY_SETUP_:

    pass

    import fidia.sample
    import fidia.traits
    import fidia.archive
    import fidia.column

    # from fidia.column import *
    # from fidia.sample import *
    from fidia.archive.archive import Archive, BasePathArchive


    from fidia.column.column_definitions import ColumnDefinition, ColumnDefinitionList, \
        FITSDataColumn, FITSHeaderColumn
    from fidia.column.columns import FIDIAColumn, FIDIAArrayColumn

    from fidia.traits.trait_registry import TraitRegistry
    from fidia.traits.trait_key import TraitKey

    from .astro_object import AstronomicalObject


    # from .sample import Sample
    # from .astro_object import AstronomicalObject
    #
    # from .column import *
    #
    # from .exceptions import *
    #
    # from .descriptions import *

    # from .archive import *
