
import numpy as np

from .archive import Archive
from ..traits import TraitKey, TraitRegistry, trait_property
from ..traits.base_traits import SpectralMap, Image, Measurement, Trait
from ..exceptions import DataNotAvailable

class ExampleSpectralMap(SpectralMap):

    def init(self):
        if self.object_id == 'Gal2':
            raise DataNotAvailable("Gal2 has no 'spectral_map'")

    trait_type = "spectral_map"

    branches_versions = {None: [None], "other": [None]}

    def preload(self):
        # Make an object have typically the same random data.
        np.random.seed(hash(self.object_id) % 500000)
        self._clean = False

    def cleanup(self):
        self._clean = True

    @property
    def shape(self):
        return 0

    @trait_property('float.array')
    def value(self):
        """TheSpectralMapDocumentation"""
        assert not self._clean
        return np.random.random((20, 20, 50))
    @trait_property('float.array')
    def variance(self):
        assert not self._clean
        return np.random.random((20, 20, 50))


class ExampleSpectralMapExtra(SpectralMap):

    trait_type = "spectral_map"

    branches_versions = {'extra': [None]}

    def preload(self):
        # Make an object have typically the same random data.
        np.random.seed(hash(self.object_id) % 500000)
        self._clean = False

    def cleanup(self):
        self._clean = True

    @property
    def shape(self):
        return 0

    @trait_property('float.array')
    def value(self):
        assert not self._clean
        return np.random.random((20, 20, 50))
    @trait_property('float.array')
    def variance(self):
        assert not self._clean
        return np.random.random((20, 20, 50))
    @trait_property('float')
    def extra_value(self):
        assert not self._clean
        return np.random.random()

    # @trait_property('string')
    # def galaxy_name(self):
    #     assert not self._clean
    #     return self.object_id

class VelocityMap(Image):

    trait_type = "velocity_map"

    @property
    def shape(self):
        return self.value.shape

    def unit(self):
        return None

    @trait_property('float.array')
    def value(self):
        # return np.random.random((5, 5))
        # return (np.random.uniform(-50, 50, [8, 10])).tolist()
        return np.random.random((20, 20))

    @trait_property('float.array')
    def variance(self):
        return np.random.random((20, 20))

class LineMap(Image):

    trait_type = "line_map"

    @property
    def shape(self):
        return self.value.shape

    def unit(self):
        return None

    @trait_property('float.array')
    def value(self):
        return np.random.random((20, 20))

    @trait_property('float.array')
    def variance(self):
        return np.random.random((20, 20))

class RedImage(Image):

    trait_type = 'image'

    qualifiers = {'red'}


    @trait_property('float.array')
    def value(self):
        return np.random.random((20, 20))

    @trait_property('float.array')
    def variance(self):
        return np.random.random((20, 20))

    @trait_property('float.array')
    def extra_property_red(self):
        return 'red'


class BlueImage(Image):
    trait_type = 'image'

    qualifiers = {'blue'}

    @trait_property('float.array')
    def value(self):
        return np.random.random((20, 20))

    @trait_property('float.array')
    def variance(self):
        return np.random.random((20, 20))

    @trait_property('float.array')
    def extra_property_blue(self):
        return 'blue'

    sub_traits = TraitRegistry()

    @sub_traits.register
    class ImageSubTrait(Image):
        trait_type = 'image'

        qualifiers = {'blue'}


        @trait_property('float.array')
        def value(self):
            return np.random.random((20, 20))


        @trait_property('float.array')
        def variance(self):
            return np.random.random((20, 20))


        @trait_property('float.array')
        def extra_property_blue(self):
            return 'blue'

    @sub_traits.register
    class RedImage(Image):
        trait_type = 'image'

        qualifiers = {'red'}

        @trait_property('float.array')
        def value(self):
            return np.random.random((20, 20))

        @trait_property('float.array')
        def variance(self):
            return np.random.random((20, 20))

        @trait_property('float.array')
        def extra_property_red(self):
            return 'red'

class Redshift(Measurement):

    trait_type = "redshift"

    @trait_property('float')
    def value(self):
        return 3.14159

    def unit(self):
        return None

class TestMissingProperty(SpectralMap):

    trait_type = "spectral_map"

    @property
    def shape(self):
        return 0

    @trait_property('float.array')
    def value(self):
        return np.random.random((20, 20, 50))
    @trait_property('float.array')
    def variance(self):
        return np.random.random((20, 20, 50))

    @trait_property('string')
    def galaxy_name(self):
        return self.object_id

class SimpleTrait(Trait):
    """Description for SimpleTrait.

    Extended documentation for SimpleTrait.

    """
    # NOTE: Tests rely on this class, so changing it will require updating the tests!

    trait_type = "simple_trait"

    @trait_property('float')
    def value(self):
        return 5.5

    @trait_property('string')
    def extra(self):
        return "Extra info"

class SimpleTraitWithSubtraits(Trait):

    # NOTE: Tests rely on this class, so changing it will require updating the tests!

    trait_type = "simple_heir_trait"

    sub_traits = TraitRegistry()

    @sub_traits.register
    class SubTrait(SimpleTrait):
        trait_type = 'sub_trait'

    @trait_property('float')
    def value(self):
        return 5.5

    @trait_property('string')
    def extra(self):
        return "Extra info"


class ExampleArchive(Archive):

    available_traits = TraitRegistry()

    def __init__(self):
        # NOTE: Tests rely on `_contents`, so changing it will require updating the tests
        self._contents = ['Gal1', 'Gal2', 'Gal3']

        # Local cache for traits
        self._trait_cache = dict()

        super().__init__()

    @property
    def contents(self):
        return self._contents

    @property
    def name(self):
        return 'ExampleArchive'


    def define_available_traits(self):
        self.available_traits.register(ExampleSpectralMap)
        self.available_traits.register(ExampleSpectralMapExtra)
        # self.available_traits[TraitKey('spectral_map', 'extra', None, 'Gal2')] = TestMissingProperty
        self.available_traits.register(LineMap)
        self.available_traits.register(VelocityMap)
        self.available_traits.register(Redshift)

        # NOTE: Tests rely on this, so changing it will require updating the tests!
        self.available_traits.register(SimpleTrait)
        self.available_traits.register(SimpleTraitWithSubtraits)
        self.available_traits.register(BlueImage)
        self.available_traits.register(RedImage)


