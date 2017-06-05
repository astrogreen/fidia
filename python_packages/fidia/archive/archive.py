from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List

# Python Standard Library Imports
from collections import OrderedDict

# Other Library Imports
import pandas as pd

# FIDIA Imports
import fidia.base_classes as bases
from ..utilities import SchemaDictionary
# import fidia.sample as sample
import fidia.traits as traits
import fidia.column as columns
import fidia.cache as cache
# Other modules within this package
# from fidia.base_classes import BaseArchive

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

__all__ = ['Archive']


class Archive(bases.Archive):
    """An archive of data."""
    column_definitions = columns.ColumnDefinitionList()

    _id = None

    trait_mappings = []

    def __init__(self):

        # Traits (or properties)
        mappings = self.trait_mappings
        assert isinstance(mappings, list)
        self.trait_mappings = traits.TraitMappingDatabase()
        self.trait_mappings.register_mapping_list(mappings)
        self._trait_cache = OrderedDict()

        self.cache = cache.DummyCache()

        self._schema = {'by_trait_type': None, 'by_trait_name': None}

        super(Archive, self).__init__()

        # Associate column instances with this archive instance
        local_columns = columns.ColumnDefinitionList()
        for alias, column in self.column_definitions:
            log.debug("Associating column %s with archive %s", column, self)
            instance_column = column.associate(self)
            local_columns.add((alias, instance_column))
        self.columns = local_columns

        self.update_trait_mappings()

    # This provides a space for an archive to set which catalog data to
    # "feature". These properties are those that would be displayed e.g. when
    # someone wants an overview of the data in the archive, or for a particular
    # object.
    feature_catalog_data = []  # type: List[traits.TraitPath]

    def update_trait_mappings(self):
        """Iterates over the trait mappings provided with this archive and, if necessary, populates any ommited fields."""
        pass

    def writeable(self):
        raise NotImplementedError("")

    @property
    def contents(self):
        return self._contents

    @contents.setter
    def contents(self, value):
        self._contents = set(value)

    @property
    def archive_id(self):
        if self._id is None:
            return repr(self)
        return self._id

    @property
    def name(self):
        raise NotImplementedError("")

    def get_full_sample(self):
        """Return a sample containing all objects in the archive."""
        # Create an empty sample, and populate it via it's private interface
        # (no suitable public interface at this time.)
        from fidia.sample import Sample
        new_sample = Sample()
        id_cross_match = pd.DataFrame(pd.Series(map(str, self.contents), name=self.name, index=self.contents))

        # For a new, empty sample, extend effectively just copies the id_cross_match into the sample's ID list.
        new_sample.extend(id_cross_match)

        # Add this archive to the set of archives associated with the sample.
        new_sample._archives = {self}
        new_sample._primary_archive = self

        # Finally, we mark this new sample as immutable.
        new_sample.mutable = False

        return new_sample

    def get_trait(self, object_id=None, trait_key=None, parent_trait=None):

        if trait_key is None:
            raise ValueError("The TraitKey must be provided.")
        if object_id is None:
            raise ValueError("The object_id must be provided.")
        trait_key = traits.TraitKey.as_traitkey(trait_key)

        # Fill in default values for any `None`s in `TraitKey`
        trait_key = self.available_traits.update_key_with_defaults(trait_key)

        # Check if we have already loaded this trait, otherwise load and cache it here.
        if (object_id, trait_key, parent_trait) not in self._trait_cache:

            # Check the size of the cache, and remove item if necessary
            # This should probably be more clever.
            while len(self._trait_cache) > 20:
                self._trait_cache.popitem(last=False)

            # Determine which class responds to the requested trait.
            # Potential for far more complex logic here in future.
            trait_class = self.available_traits.retrieve_with_key(trait_key)

            # Create the trait object and cache it
            log.debug("Returning trait_class %s", type(trait_class))
            trait = trait_class(self, trait_key, object_id=object_id, parent_trait=parent_trait)

            self._trait_cache[(object_id, trait_key, parent_trait)] = trait

        return self._trait_cache[(object_id, trait_key, parent_trait)]

    def type_for_trait_path(self, path):
        """Return the type for the provided Trait path.

        :param path:
            A sequence object containing the pieces of the "path" addressing the
            object of interest.

        This function is a shortcut to determine what kind of object one should
        expect if requesting a particular Trait or trait property as defined by
        the path provided. This is a shortcut, i.e., the Traits are not actually
        constructed. It shouldn't be considered absolutely authoritative, but
        should be close.

        Currently, this can only differentiate between a Trait and a Trait Property.
        This could be made more specific in one of several ways:

        - Have the schema include type information when it is constructed.
        - Find the appropriate class by querying the TraitMapping object
          at each level.

        """

        # Drill down the schema:
        schema = self.schema(by_trait_name=True)
        current_schema_item = schema
        for path_element in path:
            trait_key = traits.TraitKey.as_traitkey(path_element)
            current_schema_item = current_schema_item[trait_key.trait_name]

        # Decide whether the item in the schema corresponds to a Trait or TraitProperty
        if isinstance(current_schema_item, dict):
            return traits.Trait
        else:
            return traits.TraitProperty

    def can_provide(self, trait_key):
        trait_key = traits.TraitKey.as_traitkey(trait_key)
        return trait_key.trait_name in self.available_traits.get_trait_names()

    def schema(self, by_trait_name=False, data_class='all'):
        """Get the schema of this Archive.

        The Schema is provided as a set of nested dictionaries. Generally, the
        top level gives different trait_types, each of which is a dictionary.
        For each trait_type, the dictionary keys are the names of the
        TraitProperty or sub-Trait. Sub-traits have dictionaries as values,
        which have the same structure. TraitProperties have the (string) type of
        the TraitProperty as their value.

        Example:

            {
                "redshift":
                {
                    "value": 'float',
                    "variance": 'float'
                },
                "line_map-NII":
                {
                    "value": 'float.array',
                    "variance": 'float.array',
                    "source": 'string'
                },
                "line_map-Ha":
                {
                    "value": 'float.array',
                    "variance": 'float.array',
                    "source": 'string'
                },
                "velocity_map":
                {
                    "value": 'float.array',
                    "systemic_redshift":
                    {
                        "value": 'float',
                        "variance": 'float
                    }
                }
            }

        The keyword `by_trait_name` can be set to True to add an extra layer to
        the hierarchy. That layer separates out the trait_type from the combined
        trait_type + trait_qualifier, or trait_name. The above example becomes:

            {
                "redshift":
                {
                    None:
                    {
                        "value": 'float',
                        "variance": 'float'
                    },
                },
                "line_map":
                {
                    "NII":
                    {
                        "value": 'float.array',
                        "variance": 'float.array',
                        "source": 'string'
                    },
                    "Ha":
                    {
                        "value": 'float.array',
                        "variance": 'float.array',
                        "source": 'string'
                    }

                }
                "velocity_map":
                {
                    "value": 'float.array',
                    "systemic_redshift":
                    {
                        "value": 'float',
                        "variance": 'float
                    }
                }
            }

        data_class:
            One of 'all', 'catalog', or 'non-catalog'

            'all' returns the full schema.

            'catalog' returns only items which contain TraitProperties of catalog type.

            'non-catalog' returns only items which contain TraitProperties of non-catalog type.

            Both 'catalog' and 'non-catalog' will not include Traits that
            consist only of TraitProperties not matching the request.


        """

        if by_trait_name:
            # Produce a version of the schema which has trait_type and
            # trait_name combined on a single level.
            return self.full_schema(combine_levels=('trait_name', 'branch_version'), verbosity='simple', data_class=data_class)
        else:
            return self.full_schema(combine_levels=('branch_version', ), verbosity='simple', data_class=data_class)

    def full_schema(cls, include_subtraits=True, data_class='all', combine_levels=None, verbosity='data_only',
                    separate_metadata=False):

        # Handle default combine_levels argument.
        if combine_levels is None:
            combine_levels = tuple()

        # Validate verbosity arguments.
        assert verbosity in ('simple', 'data_only', 'metadata', 'descriptions')
        if verbosity == 'descriptions':
            if 'branches_versions' in combine_levels:
                raise ValueError("Schema verbosity 'descriptions' requires that " +
                                 "combine_levels not include branches_versions")

        schema = SchemaDictionary()

        # Add meta data about the archive, if requested
        if verbosity == 'descriptions':
            schema['pretty_name'] = "Pretty Name for Archive"

        if separate_metadata:
            if 'trait_name' in combine_levels:
                schema_piece = schema.setdefault('trait_names', SchemaDictionary())
            else:
                schema_piece = schema.setdefault('trait_types', SchemaDictionary())
        else:
            schema_piece = schema

        available_traits_schema = cls.available_traits.schema(
                include_subtraits=include_subtraits,
                data_class=data_class,
                combine_levels=combine_levels,
                verbosity=verbosity,
                separate_metadata=separate_metadata
            )

        schema_piece.update(available_traits_schema)

        return schema

class BasePathArchive(Archive):
    def __init__(self, **kwargs):
        self.basepath = kwargs.pop('basepath')
        super(BasePathArchive, self).__init__(**kwargs)