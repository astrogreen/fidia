from collections import OrderedDict
from sov.helpers.dummy_data.astro_object import ARCHIVE


def get_survey_objects(survey=None):
    survey_objects = []
    for key, value in ARCHIVE.items():
        if str(survey) in str(getattr(value, 'owner')):
            survey_objects.append(value)
    completed_data = dict(enumerate(survey_objects))
    return list(completed_data.values())


class Survey(object):
    def __init__(self, **kwargs):
        for field in ('id', 'name', 'objects'):
            setattr(self, field, kwargs.get(field, None))

SURVEYS = OrderedDict()

surveys = ['sami', 'gama', 'galah']

for i, s in enumerate(surveys):
    SURVEYS[s] = Survey(
        id=i,
        name=s,
        objects=get_survey_objects(survey=s)
    )


