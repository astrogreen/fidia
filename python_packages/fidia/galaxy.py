

#from .astro_object import AstroObject



class Galaxy(object):

    def __init__(self, identifier):
        self.inclination = None
        self.position_angle = None
        self._identifier = identifier

    @property
    def identifier(self):
        return self._identifier
    @identifier.setter
    def identifier(self, value):
        if self._identifier is None:
            self._identifier = value
        else:
            raise Exception("Identifiers cannot be reset")

    @property
    def velocity_map(self):
        return self._velocity_map

    @velocity_map.setter
    def velocity_map(self, value):
        self._velocity_map = value
 

