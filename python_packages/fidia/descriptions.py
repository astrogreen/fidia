

class DescriptionsDescriptor:
    def __init__(self, string=None):
        self.contents = string

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            if self.contents is not None:
                return self.contents
            else:
                return self.get_contents(instance, owner)

    def get_contents(self, instance, owner):
        return None

class PrettyName(DescriptionsDescriptor):
    pass


class Description(DescriptionsDescriptor):
    def get_contents(self, instance, owner):
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
    def get_contents(self, instance, owner):
        try:
            if hasattr(instance, 'doc') and instance.doc is not None:
                return instance.doc
            if hasattr(instance, '__doc__') and instance.__doc__ is not None:
                return instance.__doc__
        except:
            return None