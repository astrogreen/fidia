# Copyright (c) Australian Astronomical Observatory (AAO), 2018.
#
# The Format Independent Data Interface for Astronomy (FIDIA), including this
# file, is free software: you can redistribute it and/or modify it under the terms
# of the GNU Affero General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function, unicode_literals


import pytest

from typing import Type

import fidia

from fidia.traits import Trait, TraitProperty, TraitKey #, TraitPath
from fidia.archive.example_archive import ExampleArchive

from fidia.traits import validate_trait_name

from fidia.utilities import fidia_classname


@pytest.fixture(scope='module')
def example_archive(test_data_dir):
    ar = ExampleArchive(basepath=test_data_dir)
    return ar

class TestTraits:

    @pytest.fixture
    def TestTrait(self):
        class TestTrait(Trait):
            value = TraitProperty(dtype=(int), n_dim=0, optional=False)
            optional_value = TraitProperty(dtype=(int), n_dim=0, optional=True)

        return TestTrait


    def test_get_trait_properties(self, TestTrait):

        for attr in TestTrait._trait_property_slots():
            prop = getattr(TestTrait, attr)
            assert isinstance(prop, TraitProperty)

    @pytest.mark.xfail   # @TODO: Failing because descriptions aren't implemented for Traits themselves.
    def test_trait_descriptions(self, example_archive):
        test_trait = example_archive.image["red"]

        assert hasattr(test_trait, 'get_pretty_name')
        assert hasattr(test_trait, 'get_short_description')
        assert hasattr(test_trait, 'get_long_description')

        assert test_trait.get_pretty_name() == ""

        assert test_trait.get_short_description() == ""

        assert test_trait.get_long_description() == ""


    def test_trait_property_descriptions(self, example_archive):

        test_trait = example_archive.image["red"]

        # Check that a trait property has the necessary description attributes
        assert hasattr(test_trait, 'get_pretty_name')
        assert hasattr(test_trait, 'get_short_description')
        assert hasattr(test_trait, 'get_long_description')

        # Check that descriptions are set correctly:
        assert isinstance(test_trait.get_short_description("data"), str)
        assert test_trait.get_short_description("data") == ""

        # Check that descriptions are set correctly:
        assert isinstance(test_trait.get_long_description("data"), str)
        assert test_trait.get_long_description("data") == ""

        # Check that descriptions are set correctly:
        assert isinstance(test_trait.get_pretty_name("data"), str)
        assert test_trait.get_pretty_name("data") == ""


    @pytest.mark.xfail   # @TODO: Failing because descriptions/metadata not implemented
    def test_trait_documentation(self, example_archive):
        test_trait = example_archive.image["red"]

        print(type(test_trait.get_documentation))
        print(test_trait.get_documentation())
        assert "Extended documentation" in test_trait.get_documentation()
        # The description should not be in the documentation
        assert test_trait.get_description() not in test_trait.get_documentation()
        assert test_trait._documentation_format == 'markdown'

        assert "<strong>text</strong>" in test_trait.get_documentation('html')


class TestSpecificTraitsInArchives:

    @pytest.fixture
    def example_sample(self, example_archive):
        return fidia.Sample.new_from_archive(example_archive)

    @pytest.fixture
    def a_astro_object(self, example_sample):
        return example_sample['Gal1']


    def test_PixelImage_trait(self, a_astro_object):
        """Test of the PixelImage Trait (and indirectly, the RawFileColumn Column)."""

        from PIL import Image as PILImage

        img = a_astro_object.pixel_image['spectra']

        assert hasattr(img, 'bytes')

        assert isinstance(img.image, PILImage.Image)


    def test_trait_property_initialisation(self, example_archive):
        # type: (fidia.Archive) -> None

        print("Trait class initialised: {}".format(fidia.traits.FitsImageHdu._trait_init_name))

        trait = example_archive['Gal1'].fits_file['red_image'].fits_image_hdu["PRIMARY"]
        assert isinstance(trait, fidia.TraitCollection)

        assert trait._trait_init_name == fidia_classname(trait.__class__)
        # We're now sure that the Trait class initializer has been called. Check that it has done it's thing:

        for tp in trait._trait_property_slots(True):
            assert tp.name is not None

        trait.data



class TestTraitKeys:


    @pytest.fixture
    def valid_traitkey_list(self):
        return [
            ('my_trait', 'branch', 'ver'),
            ('my_trait', 'branch', 'v0.3'),
            ('my_trait', 'branch', '0.5'),
            ('my_trait', 'branch', '135134'),
            ('my_trait', 'b1.2', 'ver'),
            ('my_trait', '1.3', 'ver'),
            ('my_trait', 'other_branch', 'ver'),
            ('my_trait', 'branch', 'v1_3_5'),
            ('emission_map', None, 'v1'),
            ('emission_map', None, None),
            ('emission_map', 'b1', None)
        ]

    def test_traitkey_fully_qualified(self, valid_traitkey_list):

        # Check a selection of fully defined TraitKeys are valid (i.e. they don't raise an error)
        for t in valid_traitkey_list:
            if not None in t:
                print(t)
                TraitKey(*t)

        # Check that invalid TraitKeys raise an error on construction
        invalid_trait_types = ("3band", "my-trait")
        for t in invalid_trait_types:
            with pytest.raises(ValueError):
                print(t)
                TraitKey(t, "v0.3")

    def test_traitkey_string_construction(self):
        # Check that TraitKeys can be constructed from their strings
        TraitKey.as_traitkey("gama:stellar_masses(v0.3)")

    def test_string_traitkeys_reconstruction(self, valid_traitkey_list):
        for tk_tuple in valid_traitkey_list:
            tk = TraitKey(*tk_tuple)
            print(tk)
            assert TraitKey.as_traitkey(str(tk)) == tk

    def test_hyphen_string_roundtrip(self, valid_traitkey_list):
        for t in valid_traitkey_list:
            tk = TraitKey(*t)
            print(tk)
            hyphen_str = tk.ashyphenstr()
            print(hyphen_str)
            assert TraitKey.as_traitkey(hyphen_str) == tk

    def test_trait_key_hyphen_str_construction(self, valid_traitkey_list):
        # Check that TraitKeys can be created from their hyphen string notation:
        for t in valid_traitkey_list:
            trait_key_string = "-".join(map(str, t)).replace('None', '')
            print(trait_key_string)
            assert TraitKey.as_traitkey(trait_key_string) == TraitKey(*t)


    def test_traitkey_string_forms(self):

        test_list = [
            (TraitKey('my_trait'), 'my_trait'),
            (TraitKey('my_trait', version='v2'), 'my_trait(v2)'),
            (TraitKey('my_trait', branch='b2'), 'my_trait:b2')
        ]

        for tk, string_representation in test_list:
            assert str(tk) == string_representation

    def test_traitkey_not_fully_qualified(self):
        TraitKey('my_trait')
        TraitKey('my_trait', branch='b1')
        TraitKey('my_trait', version='v1')


    def test_convenience_trait_key_validation_functions(self):


        with pytest.raises(ValueError):
            validate_trait_name("blah:fsdf")

        with pytest.raises(ValueError):
            validate_trait_name("3var")

        with pytest.raises(ValueError):
            validate_trait_name("line_map-blue")

        validate_trait_name("blue_line_map")

# NOTE: Not yet implemented in FIDIA v0.4
#
# class TestTraitPaths:
#
#     def test_trait_path_creation(self):
#
#         # Basic creation: elements are fully qualified TraitKeys
#         tp = TraitPath([TraitKey("my_type"), TraitKey("my_sub_type")])
#         assert isinstance(tp, TraitPath)
#         for i in tp:
#             assert isinstance(i, TraitKey)
#         assert len(tp) == 2
#
#
#         # creation from string trait_keys
#         tp = TraitPath(["image-r", "wcs"])
#         assert isinstance(tp, TraitPath)
#         for i in tp:
#             assert isinstance(i, TraitKey)
#         assert len(tp) == 2
#
#
#         # creation from path string
#         tp = TraitPath("image-r/wcs")
#         assert isinstance(tp, TraitPath)
#         for i in tp:
#             assert isinstance(i, TraitKey)
#         assert len(tp) == 2

