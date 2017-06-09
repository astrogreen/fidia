from collections import OrderedDict
from search.helpers.dummy_positions import DUMMY_POSITIONS


class AstroObject(object):
    def __init__(self, **kwargs):
        for field in ('adcid', 'name', 'survey', 'surveys', 'status', 'position'):
            setattr(self, field, kwargs.get(field, None))

ARCHIVE = OrderedDict()
lower = 0
upper = 999
surveys = ['sami', 'gama', 'galah']
owners = ['public', 'team']
for i in range(lower, upper):
    # id is unique
    _adc_id = 'DC' + str(i)
    _name = surveys[i % 3] + str(DUMMY_POSITIONS[i][0])
    ARCHIVE[_adc_id] = AstroObject(
        adcid=_adc_id,
        name=_name,
        survey=surveys[i % 3],
        surveys=surveys,
        status=['new', 'released'],
        position={"ra": DUMMY_POSITIONS[i][2], "dec": DUMMY_POSITIONS[i][1]},
    )

