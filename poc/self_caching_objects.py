# Class of objects that replaces code with the resultant value when instantated

import time

from abc import ABCMeta

class trait_property(object):


    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        # try:
        #     return self.value
        # except AttributeError:
        #     self.value = self.fget(obj)
        # return self.value
        return self.fget(obj)

    # def __set__(self, obj, value):
    #     if self.fset is None:
    #         raise AttributeError("can't set attribute")
    #     self.fset(obj, value)
    #
    # def __delete__(self, obj):
    #     if self.fdel is None:
    #         raise AttributeError("can't delete attribute")
    #     self.fdel(obj)

    # def getter(self, fget):
    #     return type(self)(fget, self.fset, self.fdel, self.__doc__)
    #
    # def setter(self, fset):
    #     return type(self)(self.fget, fset, self.fdel, self.__doc__)
    #
    # def deleter(self, fdel):
    #     return type(self)(self.fget, self.fset, fdel, self.__doc__)


class SelfCachingObject(object):

    def __init__(self, *args, **kwargs):
        print("SelfCachingObject init")
        super(SelfCachingObject, self).__init__(*args, **kwargs)
        self._realise()

    def cleanup(self):
        """Any cleanup that must be done, e.g. closing file handles"""
        pass

    def preload(self):
        """Any thing that must be done before loading, e.g. opening files."""
        pass

    def _realise(self):
        traits = dict()
        print("Realising...")
        self.preload()
        # Iterate over class attributes:
        for key, obj in type(self).__dict__.iteritems():
            if isinstance(obj, trait_property):
                print("Found trait '{}'".format(key))
                traits[key] = obj
        for key, obj in self.__dict__.iteritems():
            if isinstance(obj, trait_property):
                print("Found trait '{}'".format(key))
                traits[key] = obj

        # Iterate over all traits, storing value as instance attribute:
        for key, obj in traits.iteritems():
            self.__dict__[key] = getattr(self, key)

        self.cleanup()

class TestObject(SelfCachingObject):

    def preload(self):
        # Task requiring cleanup
        self.cleaned_up = False

    def cleanup(self):
        self.cleaned_up = True

    @trait_property
    def value(self):
        # Loading which requires the initialisation and is time consuming
        if self.cleaned_up:
            raise Exception("Already cleaned up")
        time.sleep(2)
        return 'Hello world'


class Parent(object):

    def __new__(cls, *args, **kwargs):
        new_object = super(Parent, cls).__new__(cls)
        user_init = new_object.__init__
        def __init__(self, *args, **kwargs):
            print("New __init__ called")
            user_init(self, *args, **kwargs)
            self.extra()
        print("Replacing __init__")
        setattr(new_object, '__init__', __init__)
        return new_object

    def __init__(self):
        print("Original __init__ called")
        #super(Child, self).__init__()

    def extra(self):
        print("Extra called")

class Child(Parent):
    pass





# for key, value in t.__dict__.iteritems():
#     print(key)
#     if isinstance(value, trait_property):
#         print("Is trait_property")