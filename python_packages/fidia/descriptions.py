import textwrap
import re
from inspect import isclass

import pypandoc

from .utilities import classorinstancemethod

from . import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

DEFAULT_FORMAT = 'markdown'

SHORT_NAME_RE = re.compile(
    r"^[A-Z0-9_-]+$"
)

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
        # Doc-string is multiple lines. Split the description either:
        #    - at the first place there is a blank line.
        #    - at the end of the first line if there are no blank lines
        #    - at a maximum of 200 characters regardless.
        match = re.match(r"\n[ \t]*\n", doc_string)
        if match:
            # A blank line was found.
            description = doc_string[0:match.start()]
        else:
            description = doc_string.split("\n")[0]

        # Now check length
        if len(description) > 200:
            description = description[:200]
        return description
    else:
        return doc_string


def formatted(text, input_format, output_format=None):
    if output_format is None or input_format == output_format:
        # No conversion requested or necessary
        return text
    else:
        # Convert text to new format using Pandoc
        return pypandoc.convert_text(text, output_format, format=input_format)

def instance_check(obj):
    """Helper function to respect whether descriptions may be set on instances, classes or both.

    """

    if not hasattr(obj, 'descriptions_allowed'):
        # The object's class does not explicitly define what kinds of descriptions are allowed, so assume both.
        log.debug("Descriptions_allowed not set, class or instance are valid.")
        return True
    if isclass(obj) and obj.descriptions_allowed in ('both', 'class'):
        log.debug("Operating on class object '%s' and allowed." % str(obj))
        return True
    if not isclass(obj) and obj.descriptions_allowed in ('both', 'instance'):
        log.debug("Operating on instance object '%s' and allowed." % str(obj))
        return True

    # Otherwise, request to do something not allowed:
    raise ValueError("Attempt to set description field on '%s' does not match `descriptions_allowed` of '%s'"
                     % (str(obj), obj.descriptions_allowed))



class DescriptionsMixin:
    """A mix-in class which provides descriptions functionality for any class.

    Basically, there are four types of descriptions we must support:

    Pretty Name

        A formatted version of the field's name. This can contain spaces,
        retains case information, and can contain LaTeX Math (AMS) enclosed in $
        symbols. Note that in many cases, this will already be defined by the
        parent Trait class, in which case it should not be over-written.

    Short Description

        A brief description of the data, typically no more than 80 characters.
        This description need not repeat information that should already be
        obvious from the context (e.g. the name of the Trait or property), but
        might clarify what it is or it's origin as appropriate. Examples:

        - Spectroscopic redshift from GAMA Survey
        - Zenith distance at start of exposure
        - Stellar Pop. Syn. e-folding time for the exponentially declining SFH
        - Short descriptions support LaTeX Math (AMS) when enclosed in $ symbols.

    Long Description

        An in-depth description of the data. This description can be as detailed
        and extended as required. Github flavoured markdown is supported in full
        (and it's use is encouraged to make the description more readable).
        Additionally, LaTeX Math (AMS) is supported both for inline (when
        enclosed in single $ symbols), and display mode (when enclosed in double
        $$ symbols).

    Short Name

        A very short name (typically less than 8 charachters) suitable for use
        in e.g. FITS headers.

    """

    @classorinstancemethod
    def _parse_doc_string(self, doc_string):
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
            documentation_format = match.group('format')
            log.debug("Format designator found, format set to '%s'", documentation_format)
            del doc_lines[-1]
        else:
            documentation_format = DEFAULT_FORMAT
            log.debug("No format descriptor found, candidate was: `%s`", doc_lines[-1])

        # Rejoin all but the first line:
        documentation = "\n".join(doc_lines[1:])

        # Strip extra indents at the start of each line
        documentation = textwrap.dedent(documentation)

        # Rejoin first line:
        documentation = "\n".join((doc_lines[0], documentation))

        # Check if the documentation starts with the short description, and in
        # that case remove the short description from the documentation. (This
        # occurs because both the description and the documentation have been
        # set from the doc-string.)
        if documentation.startswith(self.get_description()):
            log.debug("Removing duplicated description from start of documentation")
            characters_to_trim = len(self.get_description())
            documentation = documentation[characters_to_trim:]
            doc_lines = documentation.splitlines()
            # Strip blank lines at start
            while re.match(r"^\s*$", doc_lines[0]) is not None:
                log.debug("Removing line '%s' from start of doc", doc_lines[-1])
                del doc_lines[0]
            documentation = "\n".join(doc_lines)


        # Update either the class or the instance as appropriate:
        try:
            instance_check(self)
        except ValueError:
            if isclass(self) and self.descriptions_allowed == 'instance':
                # In this case, we probably have already had an error, but do nothing.
                log.error("Cannot save parsed doc string as descriptions only allowed on instance" +
                          " and have been given the class '%s'" % self)
                pass
            if not isclass(self) and self.descriptions_allowed == 'class':
                # We have been given an instance, but descriptions are only allowed on classes, so set there.
                type(self)._documentation = documentation
                type(self)._documentation_format = documentation_format
        else:
            # In this case, the instance check passes, and it is safe to save
            # the description data on the object we have (class or instance)
            self._documentation = documentation
            self._documentation_format = documentation_format

    @classorinstancemethod
    def get_documentation(self, format=None):
        if hasattr(self, '_documentation'):
            log.info("Documentaiton found in cls._documentation")
            return formatted(self._documentation, self._documentation_format, format)
        try:
            if hasattr(self, 'doc') and self.doc is not None:
                log.info("Documentation found in cls.doc")
                self._parse_doc_string(self.doc)
                return formatted(self._documentation, self._documentation_format, format)
            if hasattr(self, '__doc__') and self.__doc__ is not None:
                log.info("Documentation found in cls.__doc__")
                self._parse_doc_string(self.__doc__)
                return formatted(self._documentation, self._documentation_format, format)
        except:
            return None

    @classorinstancemethod
    def set_documentation(self, value, format=DEFAULT_FORMAT):
        # Confirm if the requested usage (on class or instance) is allowed.
        instance_check(self)

        # Split the input into individual lines.
        input_lines = value.splitlines()

        # Rejoin all but the first line:
        documentation = "\n".join(input_lines[1:])

        # Remove leading spaces from these lines
        documentation = textwrap.dedent(documentation)

        # Rejoin the first line:
        documentation = "\n".join((input_lines[0], documentation))

        self._documentation = documentation
        self._documentation_format = format

    @classorinstancemethod
    def get_pretty_name(cls):
        if hasattr(cls, '_pretty_name'):
            return getattr(cls, '_pretty_name')

        if hasattr(cls, 'name'):
            # Instance description object have a name attribute (e.g. TraitProperties)
            return prettify(cls.name)
        else:
            # No name explicitly provided, so we do our best with the class name.
            return prettify(cls.__name__)

    @classorinstancemethod
    def set_pretty_name(self, value):
        # Confirm if the requested usage (on class or instance) is allowed.
        instance_check(self)

        self._pretty_name = value

    @classorinstancemethod
    def get_description(cls):
        if hasattr(cls, '_short_description'):
            log.debug("For object '%s', returning description from `_short_description` attribute.", cls)
            return getattr(cls, '_short_description')
        try:
            if hasattr(cls, 'doc') and cls.doc is not None:
                if "\n" in cls.doc:
                    return cls.doc.split("\n")[0]
                else:
                    return cls.doc
            if hasattr(cls, '__doc__') and cls.__doc__ is not None:
                return parse_short_description_from_doc_string(cls.__doc__)
        except:
            return None

    @classorinstancemethod
    def set_description(self, value):
        # Confirm if the requested usage (on class or instance) is allowed.
        instance_check(self)

        self._short_description = value

    @classorinstancemethod
    def get_short_name(self):
        if hasattr(self, '_short_name'):
            return self._short_name
        elif hasattr(self, 'name'):
            # TraitProperties have a 'name' attribute
            return self.name.upper()
        elif hasattr(self, 'descriptions_allowed') and self.descriptions_allowed in ('both', 'class'):
            # Use the name of the class as the short name, with munging to uppercase
            if isclass(self):
                name = self.__name__
            else:
                name = type(self).__name__
            # Convert to upper case
            name = name.upper()
            return name
        else:
            # Cannot use the name of the class, no known name for the instance
            return ""

    @classorinstancemethod
    def set_short_name(self, value):
        # Confirm if the requested usage (on class or instance) is allowed.
        instance_check(self)

        if not isinstance(value, str):
            ValueError("Short name can only be set to a string.")
        value_upper = value.upper()
        if SHORT_NAME_RE.match(value_upper) is None:
            raise ValueError("Invalid Short Name '%s': Short names can only consist of letters, numbers and underscores" % value)
        self._short_name = value_upper

    @classorinstancemethod
    def copy_descriptions_to_dictionary(self, other_dictionary):
        # type: (dict) -> None
        """Convenience function that handles copying all of the description data to a dictionary.

        This is useful for e.g. Django where we are often copying all of this
        information into a dictionary to be returned as JSON. This brings
        together all of the work in one place and reduces duplication.

        """

        other_dictionary['short_name'] = self.get_short_name()
        other_dictionary['pretty_name'] = self.get_pretty_name()
        other_dictionary['description'] = self.get_description()
        other_dictionary['html_documentation'] = self.get_documentation('html')


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
        """Return a pretty version of the Trait's qualifier."""

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
