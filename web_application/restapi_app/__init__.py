# Expose an AstroObject resource (here pure python object)
class AstroObject(object):
    def __init__(self, **kwargs):
        for field in ('id', 'asvoid', 'gamacataid', 'samiid', 'redshift', 'spectrum'):
            setattr(self, field, kwargs.get(field, None))
