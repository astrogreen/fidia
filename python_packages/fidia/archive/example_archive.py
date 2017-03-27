
import numpy as np

from astropy import units

from .archive import Archive
from ..traits import *
from ..traits.trait_property import trait_property_from_constant
from ..utilities import DefaultsRegistry
from ..exceptions import DataNotAvailable

from fidia.traits.fidiacolumn import ColumnFromData, ArrayColumnFromData


class SimpleTrait(Trait):
    """Description for SimpleTrait.

    Extended documentation for SimpleTrait.

    Some *markdown* formatted **text** and math: $\int_{\pi} f(x) dx$

    ##format: markdown
    """
    # NOTE: Tests rely on this class, so changing it will require updating the tests!

    trait_type = "simple_trait"

    branches_versions = {'default': ['ver0']}
    defaults = DefaultsRegistry('default', {'default': 'ver0'})


    @trait_property('float')
    def value(self):
        return 5.5
    value.set_description("TheValue")
    value.set_pretty_name("Value")

    @trait_property('float.array.1')
    def non_catalog_data(self):
        return [1.1, 2.2, 3.3]
    non_catalog_data.set_description("Some Non-catalog data")
    non_catalog_data.set_pretty_name("Non-catalog Data")

    @trait_property('string')
    def extra(self):
        return "Extra info"
    extra.set_description("ExtraInformation")
    extra.set_pretty_name("Extra Info")

class SimpleTraitWithSubtraits(Trait):

    # NOTE: Tests rely on this class, so changing it will require updating the tests!

    trait_type = "simple_heir_trait"

    branches_versions = {'default': ['ver0']}
    defaults = DefaultsRegistry('default', {'default': 'ver0'})

    sub_traits = TraitRegistry()

    @sub_traits.register
    class SubTrait(SimpleTrait):
        trait_type = 'sub_trait'

    @trait_property('float')
    def value(self):
        return 5.5

    @trait_property('float.array.1')
    def non_catalog_data(self):
        return [1.1, 2.2, 3.3]

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


    class ColumnDefinitions:

        object_ids = ['Gal1', 'Gal2', 'Gal3']

        blue_image = ArrayColumnFromData("blue", object_ids, np.random.random((len(object_ids),) + (20, 20)))
        blue_image_var = ArrayColumnFromData("bluevar", object_ids, np.random.random((len(object_ids),) + (20, 20)))

        red_image = ArrayColumnFromData("red", object_ids, np.random.random((len(object_ids),) + (20, 20)))
        red_image_var = ArrayColumnFromData("redvar", object_ids, np.random.random((len(object_ids),) + (20, 20)))

        spectral_cube = ArrayColumnFromData("speccube_red", object_ids,
                                            np.random.random((len(object_ids),) + (20, 20, 10)))

        redshift = ColumnFromData("redshift", object_ids, np.random.lognormal(0.1, 0.05, len(object_ids)))
        redshift.unit = units.dimensionless_unscaled



    class TraitDefinitions:
        pass



    @property
    def contents(self):
        return self._contents

    @property
    def name(self):
        return 'ExampleArchive'

    feature_catalog_data = [
        TraitPath('redshift', trait_property='value'),
        TraitPath('simple_trait', trait_property='value'),
        TraitPath('simple_trait', trait_property='extra')
    ]

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


