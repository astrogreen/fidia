import fidia
from collections import OrderedDict


def get_data_central_archive_schema():
    """
    List the data releases (FIDIA archives) currently ingested in ADC
    Returns:
    """
    # data releases (archives) organised by survey

    # print(fidia.known_archives.all())
    d = {'archives': {
        'sami': [
            {'name': 'SAMIDR1', 'archive_id': 1},
            {'name': 'SAMIDR2', 'archive_id': 4}
        ],
        'gama': [
            {'name': 'GAMADR2', 'archive_id': 2}
        ],
        'galah': [
            {'name': 'GALAHDR1', 'archive_id': 3}
        ]
    }}
    return OrderedDict(sorted(d.items(), key=lambda t: t[0]))


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
    _dc_schema = dict(get_data_central_archive_schema())
    d = {}
    for survey_key, survey_value in _dc_schema['archives'].items():
        for dr_value in survey_value:
            if str(dr_value.get('archive_id')) == str(archive_id):
                # get the archive's traits
                # print(dr_value)
                d = {'traits': fidia.traits.generic_traits.__all__}

    return OrderedDict(sorted(d.items(), key=lambda t: t[0]))


def get_astro_object_default_traits_schema(archive_id=None, astro_object=None):
    """
    Get the list of traits (returned in the same format as get_archive_trait_schema())
    that should be turned on for a particular AO
    Returns:

    """
    s = {'schema': []}
    return OrderedDict(sorted(s.items(), key=lambda t: t[0]))
