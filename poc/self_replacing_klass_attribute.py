class KlassAttributeObject:

    other_property = "hi"
    
    def __init__(self, var_name):
        self.var_name = var_name

    def __get__(self, instance, owner):
        return BoundMethodProxyObject(instance, self)

    def get_value(self, obj):
        return getattr(obj, self.var_name)

class BoundMethodProxyObject:
    def __init__(self, klass, attr):
        self.klass = klass
        self.attr = attr
    def __getattr__(self, name):
        return getattr(self.attr, name)
    def __call__(self):
        return self.attr.get_value(self.klass)

class TestObject:

    bound = KlassAttributeObject("_x")
    
    def __init__(self, val):
        self._x = val


import types

class SelfReplacingKlassAttributeObject:

    other_property = "hi"
    
    def __init__(self, var_name):
        self.var_name = var_name
        self._bound = False
        self.__get__ = type(self).__get__

    def bind(self, instance):
        self._bound = True
        self.instance = instance

    def __get__(self, instance, owner):
        if self._bound:
            return self
        else:
            bound_method = copy.copy(self)
            bound_method.bind(instance)
            return bound_method

    def __call__(self):
        if self._bound:
            return self.get_value(self.instance)
        else:
            raise TypeError("unbound method")

    def get_value(self, obj):
        return getattr(obj, self.var_name)

class Test2Object:

    bound = SelfReplacingKlassAttributeObject("_x")
    
    def __init__(self, val):
        self._x = val

