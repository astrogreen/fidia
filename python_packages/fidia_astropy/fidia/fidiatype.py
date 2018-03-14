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

from inspect import isclass, getmro



# Static list of modules whose members are to be considered top level FIDIA Trait Types.
#
# NOTE: This is a bit hacky. It would make more sense to actually separate
# modules containing FIDIA Traits from other machinery such as mixins and trait
# factories. This requires re-arranging the package structure, but is probably a
# net benefit in the long run.
# TODO: Reorganise the Traits package to separate Traits from mixins, factories and helpers.
TRAIT_MODULES = (
    'fidia.traits.galaxy_traits',
    'fidia.traits.generic_traits',
    'fidia.traits.meta_data_traits',
    'fidia.traits.smart_traits',
    'fidia.traits.stellar_traits'
)


def fidia_type(obj):
    """Determine the FIDIA Type of an object"""

    from .traits.base_trait import Trait

    # Start by making sure we are looking at an object we understand:
    if (not isinstance(obj, Trait)) and (not issubclass(obj, Trait)):
        raise ValueError("%s is not a FIDIA object" % obj)

    # Make sure we are looking at a class:
    if not isclass(obj):
        obj = type(obj)

    # Get fidia type for Trait objects:
    if issubclass(obj, Trait):

        # Iterate up the MRO looking for a class in one of the key modules
        for c in getmro(obj):
            fully_qualified_name = (c.__module__ + '.' + c.__name__)
            for mod in TRAIT_MODULES:
                if mod in c.__module__:
                    return c

            # Special case to handle a base Trait
            if fully_qualified_name == 'fidia.traits.base_trait.Trait':
                return c

