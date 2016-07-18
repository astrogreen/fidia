class DescriptionsMixin:
    """A mix-in class which provides descriptions functionality for any class.

    Basically, there are four types of descriptions we must support:

        @TODO: Finish documentation

    """

    @classmethod
    def get_documentation(cls):
        if hasattr(cls, '_documentation'):
            return getattr(cls, '_documentation')
        try:
            if hasattr(cls, 'doc') and cls.doc is not None:
                return cls.doc
            if hasattr(cls, '__doc__') and cls.__doc__ is not None:
                return cls.__doc__
        except:
            return None

    @classmethod
    def set_documentation(cls, value, format='latex'):
        cls._documentation = value
        cls._documentation_format = format

    @classmethod
    def get_pretty_name(cls):
        if hasattr(cls, '_pretty_name'):
            return getattr(cls, '_pretty_name')

        if hasattr(cls, 'trait_name'):
            # This is a trait, and we can convert the trait_name to a nicely formatted name
            name = getattr(cls, 'trait_name')
            # assert isinstance(name, str)
            # Change underscores to spaces
            name = name.replace("_", " ")
            # Make the first letters of each word capital.
            name.title()

            # Append the qualifier:
            # @TODO: write this bit.
            return name


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