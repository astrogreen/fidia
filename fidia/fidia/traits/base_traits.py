from .abstract_base_traits import *


class Measurement(AbstractMeasurement): pass

class Velocity(Measurement): pass

class Map(Base2DTrait):
	"""Maps provide "relative spatial information", i.e. they add spatial
	 information to existing data, such as a set of spectra or classifications.
	 For relative spatial information to be meaningful, there must be at least
	 two pieces of information. Therefore, we define map as a list of other
	 objects which also have spatial information.

	 """


	# A list of positions
	@property
	def spatial_information(self):
	    return self._spatial_information
	
	# The centre, starting point, or other canonical position information
	@property
	def nominal_position(self):
	    return self._nominal_position
	

class Spectrum(Base1DTrait, Measurement): pass

class Epoch(Measurement):

    @property
    def epoch(self):
        return self


class TimeSeries(Base1DTrait, Epoch): pass


class Image(Map): pass


class SpectralCube(Base3DTrait): pass





