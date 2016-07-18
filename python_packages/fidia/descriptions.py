from . import slogging
log = slogging.getLogger(__name__)
log.enable_console_logging()
log.setLevel(slogging.DEBUG)


class DescriptionsDescriptor:

    def __get__(self, instance, klass):
        try:
            if instance is None:
                return klass._descriptive_data[self.attribute_name]
            elif instance is not None:
                return instance._descriptive_data[self.attribute_name]
        except (KeyError, AttributeError):
            return self.get_contents(instance, klass)

    def __set__(self, instance, value):
        raise Exception("Descriptive information cannot be set in this way. Programming Error.")

    def get_contents(self, instance, klass):
        return None

class PrettyName(DescriptionsDescriptor):
    attribute_name = "pretty_name"


class Description(DescriptionsDescriptor):
    attribute_name = "description"
    def get_contents(self, instance, klass):
        try:
            if hasattr(instance, 'doc') and instance.doc is not None:
                if "\n" in instance.doc:
                    return instance.doc.split("\n")[0]
                else:
                    return instance.doc
            if hasattr(instance, '__doc__') and instance.__doc__ is not None:
                if "\n" in instance.__doc__:
                    return instance.__doc__.split("\n")[0]
                else:
                    return instance.__doc__
        except:
            return None


class Documentation(DescriptionsDescriptor):
    attribute_name = "documentation"
    def get_contents(self, instance, klass):
        if instance is None:
            object = klass
        else:
            object = instance

        try:
            if hasattr(object, 'doc') and object.doc is not None:
                return object.doc
            if hasattr(object, '__doc__') and object.__doc__ is not None:
                return object.__doc__
        except:
            return None

class ShortName(DescriptionsDescriptor):
    attribute_name = "short_name"

    def get_contents(self, instance, klass):
        if instance is None:
            object = klass
        else:
            object = instance

        return object.__name__
