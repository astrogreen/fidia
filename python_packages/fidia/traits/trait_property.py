# Standard Library Imports
from abc import ABCMeta

# Internal package imports
from ..exceptions import *
from ..descriptions import DescriptionsMixin

# Logging import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.enable_console_logging()
log.setLevel(slogging.WARNING)



def trait_property(func_or_type):
    """Decorate a function which provides an individual property of a trait.

    This has an optional data-type designation. It can be used in one of two ways:

    @trait_property
    def value(self):
        return 5

    @trait_property('float')
    def value(self):
        return 5.5

    Implementation:

        Because the two examples actually look a bit different internally,
        this is implemented as a function that determines which case has been
        given. If the argument is callable, then it is assumed to be the first
        example, above, and if the argument is a string, then it is assumed to be
        the second example above.

    """""
    if isinstance(func_or_type, str):
        # Have been given a data type, so return a decorator:
        log.debug("Decorating trait_property with data-type %s", func_or_type)
        tp = TraitProperty(type=func_or_type)
        return tp.loader
    elif callable(func_or_type):
        # Have not been given a data type. Build the property directly:
        return TraitProperty(func_or_type)
    raise Exception("trait_property decorator used incorrectly. Check documentation.")


class TraitProperty(DescriptionsMixin, metaclass=ABCMeta):

    allowed_types = [
        'string',
        'float',
        'int',
        'string.array',
        'float.array',
        'int.array'
    ]

    descriptions_allowed = 'instance'

    def __init__(self, fload=None, fset=None, fdel=None, doc=None, type=None, name=None):
        self.fload = fload
        self.fset = fset
        self.fdel = fdel

        if name is None and fload is not None:
            name = fload.__name__
        self.name = name
        if doc is None and fload is not None:
            doc = fload.__doc__
        self.doc = doc

        # @TODO: Note that the type must be defined for now, should inherit from Trait parent class.
        self.type = type

    def loader(self, fload):
        """Decorator which sets the loader function for this TraitProperty"""
        if self.name is None:
            self.name = fload.__name__
        log.debug("Setting loader for TraitProperty '%s'", self.name)
        if self.doc is None:
            self.doc = fload.__doc__
        self.fload = fload
        return self

    @property
    def type(self):
        return self._type
    @type.setter
    def type(self, value):
        if value not in self.allowed_types:
            raise Exception("Trait property type '{}' not valid".format(value))
        self._type = value

    @property
    def doc(self):
        return self.__doc__
    @doc.setter
    def doc(self, value):
        self.__doc__ = value

    def __get__(self, instance, instance_type):
        if instance is None:
            return self
        else:
            log.debug("Creating a bound trait property '%s.%s'", instance_type.__name__, self.name)
            return BoundTraitProperty(instance, self)


class BoundTraitProperty:

    def __init__(self, trait, trait_property):
        self._trait = trait
        self._trait_property = trait_property

    def __getattr__(self, item):
        """Pass most undefined attribute requests to the host TraitProperty.

        Note that any method or attribute explicitly defined in this class will
        override the host TraitProperty's attributes.

        """
        if item not in ('loader',) and not item.startswith("_"):
            return getattr(self._trait_property, item)

    @property
    def name(self):
        return self._trait_property.name

    @property
    def type(self):
        return self._trait_property.type

    @property
    def doc(self):
        return self._trait_property.doc

    def __call__(self):
        """Retrieve the value of this TraitProperty"""
        return self.value

    @property
    def value(self):
        """The value of this TraitProperty, retrieved using cache requests.

        The value is retrieved from the cache stack of the archive to which this
        TraitProperty (and therefore Trait) belong to. At the bottom of the
        cache stack (i.e. if no cache has the necessary data), the request is
        passed back to the `uncached_value` property of this TraitProperty.
        """

        return self._trait.archive.cache.cache_request(self._trait, self.name)

    @property
    def uncached_value(self):
        """Retrieve the trait property value via the user provided loader.

        The preload and cleanup functions of the Trait are called if present
        before and after running the loader.

        """

        log.debug("Loading data for get for TraitProperty '%s'", self.name)


        # try...except block to handle attempting to preload the trait. If the
        # preload fails, then we assume that the cleanup does not need to be called.
        try:

            # Preload the Trait if necessary.
            self._trait._load_incr()
        except DataNotAvailable:
            raise
        except Exception as e:
            log.exception("An exception occurred trying to preload Trait %s",
                          self._trait.trait_key
                          )
            raise DataNotAvailable("An unexpected error occurred trying to retrieve the requested data.")

        # Now, the Trait has been successfully preloaded. Here is another
        # try...except block, which will make sure the Trait is cleaned up
        # even if the TraitProperty can't be retrieved.

        try:
            # Call the actual user defined loader function to get the value of the TraitProperty.
            value = self._trait_property.fload(self._trait)
        except DataNotAvailable:
            raise
        except Exception as e:
            log.exception("An unexpected exception occurred trying to retrieve the TraitProperty %s of Trait %s",
                          self._trait_property.name,
                          self._trait.trait_key
                          )
            raise DataNotAvailable("An error occurred trying to retrieve the requested data.")
        finally:
            # Finally because we have definitely successfully run the
            # preload command, we must run the cleanup even if there was an error.

            # Cleanup the Trait if necessary.
            self._trait._load_decr()

        return value

# Register `BoundTraitProperty` as a subclass of `TraitProperty`. This makes
# `isinstance(value, TraitProperty)` work as expected for `TraitProperty`s that have
# been bound to their `Trait`.
TraitProperty.register(BoundTraitProperty)

def trait_property_from_fits_header(header_card_name, type, name):

    tp = TraitProperty(type=type, name=name)

    tp.fload = lambda self: self._header[header_card_name]
    tp.set_short_name(header_card_name)

    # # @TODO: Providence information can't get filename currently...
    # tp.providence = "!: FITS-Header {{file: '{filename}' extension: '{extension}' header: '{card_name}'}}".format(
    #     card_name=header_card_name, extension=extension, filename='UNDEFINED'
    # )

    return tp
