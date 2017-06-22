import fidia
from collections import OrderedDict


def get_sov_schema(astro_object=None):
    """
    return sov schema for astroobject
    Args:
        astro_object:

    Returns:

    """
    # _s = {'archives': {}}
    _s = {}
    _s.update(get_data_central_archive_schema())

    for archive in _s["archives"]:
        archive.update(get_archive_trait_schema(archive_id=archive.get('archive_id')))

    return OrderedDict(sorted(_s.items(), key=lambda t: t[0]))


def get_sov_defaults_schema(astro_object=None):
    """
    return sov defaults for schema for astroobject
    Args:
        astro_object:

    Returns:

    """
    defaults = {
        "traits": [
            {'name': 'trait1', 'trait_class': 'image', 'archive_id': 1},
            {'name': 'trait2', 'trait_class': 'table', 'archive_id': 1}
        ]
    }
    return OrderedDict(sorted(defaults.items(), key=lambda t: t[0]))


def get_data_central_archive_schema():
    """
    List the data releases (FIDIA archives) currently ingested in ADC
    Returns:
    """
    # data releases (archives) organised by survey

    # print(fidia.known_archives.all())
    d = {
        'archives': [
            {'name': 'SAMIDR1', 'archive_id': 1, 'survey': 'sami'},
            {'name': 'SAMIDR2', 'archive_id': 4, 'survey': 'sami'},
            {'name': 'GAMADR2', 'archive_id': 2, 'survey': 'gama'},
            {'name': 'GALAHDR1', 'archive_id': 3, 'survey': 'galah'}
        ]
    }
    return OrderedDict(sorted(d.items(), key=lambda t: t[0]))


def get_format_for_trait_class(trait_class):
    if trait_class == "Image":
        return ["jpg"]
    if trait_class == "Table":
        return ["csv", "ascii", "votable"]
    return ["fits"]


def get_archive_trait_schema(archive_id=None):
    """
    All available traits for an archive
    Used to populate the control panel of the SOV (though all will be
    unchecked, use the get_astro_object_default_traits_schema() to figure out which
    should be on by default).
    Args:
        archive_id:

    Returns:

    """
    _trait_classes = fidia.traits.generic_traits.__all__
    _traits = []
    for t in _trait_classes:
        _traits.append(
            {'name': 'trait1', 'trait_class': t.lower(), 'formats': get_format_for_trait_class(t), 'description': 'very short description'})
        _traits.append({'name': 'trait2', 'trait_class': t.lower(), 'formats': get_format_for_trait_class(t),
                        'description': 'very short description'})

    _dc_schema = dict(get_data_central_archive_schema())
    d = {}
    for archive in _dc_schema["archives"]:
        if str(archive.get('archive_id')) == str(archive_id):
            # TODO get the archive's traits
            d = {'traits': _traits}

    return OrderedDict(sorted(d.items(), key=lambda t: t[0]))


def get_astro_object_default_traits_schema(archive_id=None, astro_object=None):
    """
    Get the list of traits (returned in the same format as get_archive_trait_schema())
    that should be turned on for a particular AO
    Returns:

    """
    s = {'schema': []}
    return OrderedDict(sorted(s.items(), key=lambda t: t[0]))

