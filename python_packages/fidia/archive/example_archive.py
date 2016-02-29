
import numpy as np

from .archive import Archive
from ..traits.utilities import TraitKey, TraitMapping, trait_property
from ..traits.base_traits import SpectralMap, Image, Measurement, Trait
from ..exceptions import DataNotAvailable

class ExampleSpectralMap(SpectralMap):

    # def init(self):
    #     if self.trait_name != 'mymap':
    #         raise DataNotAvailable("ExampleSpectraMap only has trait_name='mymap' data.")

    trait_type = "spectral_map"

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        return [TraitKey(cls.trait_type, trait_name="", version="")]

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
        return np.random.random((3, 5, 10))
    @trait_property('float.array')
    def variance(self):
        assert not self._clean
        return np.random.random((3, 5, 10))


class ExampleSpectralMapExtra(SpectralMap):

    trait_type = "spectral_map"

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        return [TraitKey(cls.trait_type, trait_name="", version="")]

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
        return np.random.random((3, 5, 10))
    @trait_property('float.array')
    def variance(self):
        assert not self._clean
        return np.random.random((3, 5, 10))
    @trait_property('float')
    def extra_value(self):
        assert not self._clean
        return np.random.random()

    @trait_property('string')
    def galaxy_name(self):
        assert not self._clean
        return self.object_id

class VelocityMap(Image):

    trait_type = "velocity_map"

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        return [TraitKey(cls.trait_type, trait_name="", version="")]

    @property
    def shape(self):
        return self.value.shape

    def unit(self):
        return None

    @trait_property('float.array')
    def value(self):
        return np.random.random((5, 5))
        #return np.random.random((50, 50))

    @trait_property('float.array')
    def variance(self):
        return np.random.random((5, 5))

class LineMap(Image):

    trait_type = "line_map"

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        return [TraitKey(cls.trait_type, trait_name="", version="")]

    @property
    def shape(self):
        return self.value.shape

    def unit(self):
        return None

    @trait_property('float.array')
    def value(self):
        return np.random.random((5, 5))

    @trait_property('float.array')
    def variance(self):
        return np.random.random((5, 5))

class Redshift(Measurement):

    trait_type = "redshift"

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        return [TraitKey(cls.trait_type, trait_name="", version="")]

    @trait_property('float')
    def value(self):
        return 3.14159

    def unit(self):
        return None

class TestMissingProperty(SpectralMap):

    trait_type = "spectral_map"

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        return [TraitKey(cls.trait_type, trait_name="", version="")]

    @property
    def shape(self):
        return 0

    @trait_property('float.array')
    def value(self):
        return np.random.random((3, 5, 10))
    @trait_property('float.array')
    def variance(self):
        return np.random.random((3, 5, 10))

    @trait_property('string')
    def galaxy_name(self):
        return self.object_id

class SimpleTrait(Trait):

    # NOTE: Tests rely on this class, so changing it will require updating the tests!

    trait_type = "simple_trait"

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        return [TraitKey(cls.trait_type, trait_name="", version="")]

    @trait_property('float')
    def value(self):
        return 5.5

    @trait_property('string')
    def extra(self):
        return "Extra info"

class SimpleTraitWithSubtraits(Trait):

    # NOTE: Tests rely on this class, so changing it will require updating the tests!

    trait_type = "simple_heir_trait"

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        return [TraitKey(cls.trait_type, trait_name="", version="")]

    _sub_traits = TraitMapping()
    _sub_traits[TraitKey('sub_trait')] = SimpleTrait

    @trait_property('float')
    def value(self):
        return 5.5

    @trait_property('string')
    def extra(self):
        return "Extra info"


class ExampleArchive(Archive):

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
        self.available_traits[TraitKey('spectral_map', None, None, None)] = ExampleSpectralMap
        self.available_traits[TraitKey('spectral_map', 'extra', None, None)] = ExampleSpectralMapExtra
        self.available_traits[TraitKey('spectral_map', 'extra', None, 'Gal2')] = TestMissingProperty
        self.available_traits[TraitKey('line_map', None, None, None)] = LineMap
        self.available_traits[TraitKey('velocity_map', None, None, None)] = VelocityMap
        self.available_traits[TraitKey('redshift', None, None, None)] = Redshift

        # NOTE: Tests rely on this, so changing it will require updating the tests!
        self.available_traits[TraitKey('simple_trait', None, None, None)] = SimpleTrait
        self.available_traits[TraitKey('simple_heir_trait', None, None, None)] = SimpleTraitWithSubtraits


        return self.available_traits
