class AstronomicalObject(object):

    def __init__(self, identifier=None, ra=None, dec=None):
        if identifier is None:
            if ra is None or dec is None:
                raise Exception("Either 'identifier' or 'ra' and 'dec' must be defined.")
            self._identifier = "J{ra:3.6}{dec:+2.4d}".format(ra=ra, dec=dec)
        else:
            self._identifier = identifier

        self._ra = ra
        self._dec = dec


    @property
    def identifier(self):
        return self._identifier

    @property
    def ra(self):
        return self._ra

    @property
    def dec(self):
        return self._dec
    
    
     