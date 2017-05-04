# Standard Library Imports
from abc import ABCMeta
import re
import inspect

# Internal package imports
from ..exceptions import *
from ..descriptions import DescriptionsMixin
from ..utilities import RegexpGroup

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

    allowed_types = RegexpGroup(
        'string',
        'float',
        'int',
        re.compile(r"string\.array\.\d+"),
        re.compile(r"float\.array\.\d+"),
        re.compile(r"int\.array\.\d+"),
        # # Same as above, but with optional dimensionality
        # re.compile(r"string\.array(?:\.\d+)?"),
        # re.compile(r"float\.array(?:\.\d+)?"),
        # re.compile(r"int\.array(?:\.\d+)?"),
    )

    catalog_types = [
        'string',
        'float',
        'int'
    ]

    non_catalog_types = RegexpGroup(
        re.compile(r"string\.array\.\d+"),
        re.compile(r"float\.array\.\d+"),
        re.compile(r"int\.array\.\d+")
        # # Same as above, but with optional dimensionality
        # re.compile(r"string\.array(?:\.\d+)?"),
        # re.compile(r"float\.array(?:\.\d+)?"),
        # re.compile(r"int\.array(?:\.\d+)?"),
    )

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

    def get_formatted_units(self):
        log.debug("get_formatted_units()")
        # This is a nearly identical copy of the code in base_trait.py::Trait

        log.debug("%s has '_trait': %s", self, hasattr(self, '_trait'))

        # These few lines "inherit" the parent Trait's units in some circumstances.
        if (not hasattr(self, 'unit')) \
                and hasattr(self, '_trait') \
                and hasattr(self._trait, 'unit'):
            # Parent Trait is known and has units.
            log.debug("Unit inheritance possible")
            if self.name == 'value':
                log.debug("Inheriting unit from trait.")
                self.unit = self._trait.unit

        if hasattr(self, 'unit'):
            if hasattr(self.unit, 'value'):
                formatted_unit = "{0.unit:latex_inline}".format(self.unit)
                # formatted_unit = "{0.unit}".format(cls.unit)
            else:
                try:
                    formatted_unit = self.unit.to_string('latex_inline')
                    # formatted_unit = cls.unit.to_string()
                except:
                    log.exception("Unit formatting failed for unit %s of trait %s, trying plain latex", self.unit, self)
                    try:
                        formatted_unit = self.unit.to_string('latex')
                    except:
                        log.exception("Unit formatting failed for unit %s of trait %s, trying plain latex", self.unit, self)
                        raise
                        formatted_unit = ""

            log.info("Units formatting before modification for trait %s: %s", str(self), formatted_unit)

            # For reasons that are not clear, astropy puts the \left and \right
            # commands outside of the math environment, so we must fix that
            # here.
            #
            # In fact, it appears that the units code is quite buggy.
            # @TODO: Review units code!
            if formatted_unit != "":
                formatted_unit = formatted_unit.replace("\r", "\\r")
                if not formatted_unit.startswith("$"):
                    formatted_unit = "$" + formatted_unit
                if not formatted_unit.endswith("$"):
                    formatted_unit = formatted_unit + "$"
                formatted_unit = re.sub(r"\$\\(left|right)(\S)\$", r"\\\1\2", formatted_unit)
                if not formatted_unit.startswith("$"):
                    formatted_unit = "$" + formatted_unit
                if not formatted_unit.endswith("$"):
                    formatted_unit = formatted_unit + "$"

                formatted_unit = formatted_unit.replace("{}^{\\prime\\prime}", "arcsec")

            # Return the final value, with the multiplier attached
            if hasattr(self.unit, 'value'):
                formatted_unit = "{0.value:0.03g} {1}".format(self.unit, formatted_unit)
            log.info("Units final formatting for trait %s: %s", str(self), formatted_unit)
            return formatted_unit
        else:
            return ""


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

    def __repr__(self):
        return "<TraitProperty {}>".format(self.name)


class BoundTraitProperty:

    def __init__(self, trait, trait_property):
        self._trait = trait
        self._trait_property = trait_property

    def __getattr__(self, item):
        """Pass most undefined attribute requests to the host TraitProperty.

        Note that any method or attribute explicitly defined in this class will
        override the host TraitProperty's attributes.

        """
        if item not in ('loader',) and not item.startswith("__"):
            # First check if the item is defined on the TraitProperty class.
            if item in dir(TraitProperty):
                # Get the item from the class. Note, we cannot use getattr here,
                # or we may inadvertently call the descriptor logic early.
                #
                # (Otherwise, there is very strange interactions between this
                # code and classorinstancemethod in utilities.py)
                classitem = inspect.getattr_static(TraitProperty, item)
                if hasattr(classitem, '__get__'):
                    # Item is a descriptor. Bind it to this object (instead of the original TraitProperty)
                    return classitem.__get__(self, BoundTraitProperty)
                else:
                    return classitem
            # Otherwise, item must be an instance attribute
            attr = getattr(self._trait_property, item)

            return attr

    def __repr__(self):
        return "<BoundTraitProperty {} of {}>".format(self._trait_property.name, str(self._trait.trait_key))

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

def trait_property_from_constant(const_value, type, name):
    tp = TraitProperty(type=type, name=name)
    tp.fload = lambda self: const_value
    return tp