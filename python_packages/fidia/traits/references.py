from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Type
import fidia

# Python Standard Library Imports

# Other Library Imports

# FIDIA Imports
from fidia.exceptions import *
# from fidia.column import ColumnID
from fidia.base_classes import AbstractBaseTrait
from fidia.traits.trait_key import TraitKey
# Other modules within this package

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

# __all__ = []

# noinspection PyPep8Naming
class column_reference(object):

    def __init__(self, column_id_or_alias):
        if column_id_or_alias is None:
            raise FIDIAException("a column reference must provide either a column id or an alias.")
        self.column_id_or_alias = column_id_or_alias
        self.column_id = None

    def is_resolved(self):
        return self.column_id is not None



class TraitPointer(object):
    def __init__(self, archive, astro_object, trait_class=None, trait_keys_dict=dict()):
        self._trait_class = None  # type: Type[fidia.Trait]

        self._archive = archive  # type: fidia.archive.archive.Archive
        self._astro_object = astro_object  # type: fidia.astro_object.AstronomicalObject
        self._trait_registry = None  # type: fidia.traits.trait_registry.TraitRegistry

        self._trait_keys_dict = trait_keys_dict  # type: dict


        self.trait_class = trait_class

    @property
    def trait_class(self):
        return self._trait_class

    @trait_class.setter
    def trait_class(self, value):
        assert issubclass(value, AbstractBaseTrait)
        self._trait_class = value  # type: fidia.Trait

    def __getitem__(self, item):
        tk = TraitKey.as_traitkey(item)

        if not (
                tk.trait_name in self._trait_keys_dict
                and tk.branch in self._trait_keys_dict[tk.trait_name]
                and tk.version in self._trait_keys_dict[tk.trait_name][tk.branch]):
            raise UnknownTrait("%s", str(tk))

        trait = self._trait_class(archive, trait_key, object_id, parent_trait)

        return trait

    # def _set_branch_and_version(self, trait_key):
    #     """Trait Branch and Version handling:
    #
    #     The goal of this is to set the trait branch and version if at all possible. The
    #     following are tried:
    #     - If version explicitly provided in this initialisation, that is the version.
    #     - If this is a sub trait check the parent trait for it's version.
    #     - If the version is still none, try to set it to the default for this trait.
    #     """
    #
    #     # if log.isEnabledFor(slogging.DEBUG):
    #     assert isinstance(trait_key, TraitKey)
    #
    #     def validate_and_inherit(trait_key, parent_trait, valid, attribute):
    #         """Helper function to validate and/or inherit.
    #
    #         This is defined because the logic is identical for both branches
    #         and versions, so this avoides repetition
    #
    #         """
    #
    #         current_value = getattr(trait_key, attribute)
    #
    #         if current_value is not None:
    #             # We have been given a (branch/version) value, check that it
    #             # is valid for this Trait:
    #             if valid is not None:
    #                 assert current_value in valid, \
    #                     "%s '%s' not valid for trait '%s'" % (attribute, current_value, self)
    #             return current_value
    #         elif current_value is None:
    #             # We have been asked to inherit the branch/version from the
    #             # parent trait. If the parent_trait is defined (i.e. this is
    #             # not a top level trait), then take its value if it is valid
    #             # for this trait.
    #             if parent_trait is not None:
    #                 parent_value = getattr(parent_trait, attribute)
    #                 # This is a sub trait. Inherit branch from parent unless not valid.
    #                 if valid is None:
    #                     # All options are valid.
    #                     return parent_value
    #                 elif valid is not None and parent_value in valid:
    #                     return parent_value
    #                 else:
    #                     # Parent is not valid here, so leave as None
    #                     return None
    #
    #     # Determine the branch given the options.
    #     self.branch = validate_and_inherit(trait_key, self._parent_trait, self.branches_versions, 'branch')
    #
    #     # Now that the branch has been specified, determine the valid versions
    #     if self.branches_versions is not None:
    #         valid_versions = self.branches_versions[self.branch]
    #     else:
    #         valid_versions = None
    #
    #     # Determine the version given the options
    #     self.version = validate_and_inherit(trait_key, self._parent_trait, valid_versions, 'version')
