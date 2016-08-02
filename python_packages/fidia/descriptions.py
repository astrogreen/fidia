import textwrap
import re
from inspect import isclass

import pypandoc

from .utilities import classorinstancemethod

from . import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

DEFAULT_FORMAT = 'markdown'

def prettify(string):
    # type: (str) -> str
    """Reformat a string to be more human readable."""

    # @TODO: Add support for CamelCase.

    # Change underscores to spaces
    result = string.replace("_", " ")
    # Make the first letters of each word capital.
    result = result.title()

    return result

def parse_short_description_from_doc_string(doc_string):
    """Get a short description from the first line of a doc-string."""
    if "\n" in doc_string:
        return doc_string.split("\n")[0]
    else:
        return doc_string


def formatted(text, input_format, output_format=None):
    if output_format is None or input_format == output_format:
        # No conversion requested or necessary
        return text
    else:
        # Convert text to new format using Pandoc
        return pypandoc.convert_text(text, output_format, format=input_format)


class DescriptionsMixin:
    """A mix-in class which provides descriptions functionality for any class.

    Basically, there are four types of descriptions we must support:

        @TODO: Finish documentation

    """

    @classmethod
    def _parse_doc_string(cls, doc_string):
        """Take a doc string and parse it for documentation."""
        log.debug("Parsing doc string: \n'''%s'''", doc_string)

        doc_lines = doc_string.splitlines()

        # Strip blank lines at end
        while re.match(r"^\s*$", doc_lines[-1]) is not None:
            log.debug("Removing line '%s' from end of doc", doc_lines[-1])
            del doc_lines[-1]

        # Check for a format designator at the end.
        match = re.match(r"^\s*#+format: (?P<format>\w+)\s*$", doc_lines[-1])
        if match:
            cls._documentation_format = match.group('format')
            log.debug("Format designator found, format set to '%s'", cls._documentation_format)
            del doc_lines[-1]
        else:
            cls._documentation_format = DEFAULT_FORMAT
            log.debug("No format descriptor found, candidate was: `%s`", doc_lines[-1])

        # Rejoin all but the first line:
        documentation = "\n".join(doc_lines[1:])

        # Strip extra indents at the start of each line
        documentation = textwrap.dedent(documentation)

        # Rejoin first line:
        documentation = "\n".join((doc_lines[0], documentation))

        cls._documentation = documentation

    @classmethod
    def get_documentation(cls, format=None):
        if hasattr(cls, '_documentation'):
            log.info("Documentaiton found in cls._documentation")
            return formatted(cls._documentation, cls._documentation_format, format)
        try:
            if hasattr(cls, 'doc') and cls.doc is not None:
                log.info("Documentation found in cls.doc")
                cls._parse_doc_string(cls.doc)
                return formatted(cls._documentation, cls._documentation_format, format)
            if hasattr(cls, '__doc__') and cls.__doc__ is not None:
                log.info("Documentation found in cls.__doc__")
                cls._parse_doc_string(cls.__doc__)
                return formatted(cls._documentation, cls._documentation_format, format)
        except:
            return None

    @classmethod
    def set_documentation(cls, value, format=DEFAULT_FORMAT):
        cls._documentation = value
        cls._documentation_format = format

    @classmethod
    def get_pretty_name(cls):
        if hasattr(cls, '_pretty_name'):
            return getattr(cls, '_pretty_name')

        # No name explicitly provided, so we do our best with the class name.
        return prettify(cls.__name__)

    @classmethod
    def set_pretty_name(cls, value):
        cls._pretty_name = value

    @classmethod
    def get_description(cls):
        if hasattr(cls, '_short_description'):
            return getattr(cls, '_short_description')
        try:
            if hasattr(cls, 'doc') and cls.doc is not None:
                if "\n" in cls.doc:
                    return cls.doc.split("\n")[0]
                else:
                    return cls.doc
            if hasattr(cls, '__doc__') and cls.__doc__ is not None:
                if "\n" in cls.__doc__:
                    return cls.__doc__.split("\n")[0]
                else:
                    return cls.__doc__
        except:
            return None

    @classmethod
    def set_description(cls, value):
        cls._short_description = value

class TraitDescriptionsMixin(DescriptionsMixin):
    """Extends Descriptions Mixin to include support for qualifiers on Traits

     The qualifiers aren't known until the Trait is instantated, so these must
     be handled differently.

     This mixin is only valid for Trait classes.

     IMPLEMENTATION NOTES:

        The functions of this mixin are designed to work on either a class or an
        instance and behave sensibly in either case. Therefore this class uses
        the non-built-in `classsorisntancemethod`, and then within each method
        decides if it has been handed a class or an instance.

     """

    @classorinstancemethod
    def get_qualifier_pretty_name(self, qualifier=None):
        """Return the pretty name for this Trait, building it from the Trait type and qualifier if necessary."""

        # This function is designed to work on either a class or an instance.
        #
        # To reduce duplication of code, all of the work is implemented for the case
        # that it has been called as a class method. If it is called as an
        # instance method, then it simply calls the class method with the appropriate arguments.

        if isclass(self) and qualifier is None:
            raise ValueError("Must provide qualifier for which to return pretty name")

        elif isclass(self) and qualifier not in self.qualifiers:
            raise ValueError("Qualifier provided is not valid for Trait class '%s'" % str(self))

        elif isclass(self):
            # This is a class and we've been given a valid qualifier to provide the pretty name for
            if hasattr(self, '_pretty_name_qualifiers') and qualifier in self._pretty_name_qualifiers:
                # A pretty name has been explicilty defined
                return self._pretty_name_qualifiers[qualifier]
            else:
                # No pretty name defined, so prettify the qualifier
                return prettify(qualifier)

        else:
            # This is an instance of a Trait, so we know the qualifier.
            # Therefore, call this function as a class method and explicitly
            # provide the trait_qualifier
            return type(self).get_qualifier_pretty_name(self.trait_qualifier)

    @classorinstancemethod
    def get_pretty_name(self, qualifier=None):
        """Return a pretty version of the Trait's name, including the qualifier if present.

        Note, this overrides a class method which would just return a pretty
        version of the trait_type alone. So if this method is called on the
        class, one gets only that.

        """

        # This function is designed to work on either a class or an instance.
        #
        # To reduce duplication of code, all of the work is implemented for the case
        # that it has been called as a class method. If it is called as an
        # instance method, then it simply calls the class method with the appropriate arguments.

        if isclass(self) and qualifier is None:
            # No qualifier is present/available
            if hasattr(self, '_pretty_name'):
                # Pretty name explicitly defined
                return getattr(self, '_pretty_name')
            else:
                # Pretty name not explicitly defined
                # Because this is a trait, and we can convert the trait_type to a nicely formatted name
                return prettify(getattr(self, 'trait_type'))

        elif isclass(self) and qualifier not in self.qualifiers:
            # A qualifier has been provided, but isn't known to this class.
            raise ValueError("Qualifier provided is not valid for Trait class '%s'" % str(self))

        elif isclass(self):
            # This is a class, and the trait_qualifier has been explicitly provided

            # Get the pretty name for this Trait class without a qualifier:
            name = self.get_pretty_name(None)

            # Append the pretty name for the qualifier
            name += " — " + self.get_qualifier_pretty_name(qualifier)

            return name

        else:
            # This is an instance of a Trait, so we know the qualifier.
            # Therefore, call this function as a class method and explicitly
            # provide the trait_qualifier
            return type(self).get_pretty_name(self.trait_qualifier)


    @classmethod
    def set_pretty_name(cls, value, **kwargs):
        cls._pretty_name = value
        for key in kwargs:
            if key not in cls.qualifiers:
                raise KeyError("'%s' is not a qualifier of trait '%s'" % (key, cls))
        if not hasattr(cls, '_pretty_name_qualifiers'):
            cls._pretty_name_qualifiers = dict()
        cls._pretty_name_qualifiers.update(kwargs)
