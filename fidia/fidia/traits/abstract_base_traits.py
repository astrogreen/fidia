"""
# Traits in FIDIA

Traits are the properties of astronomical object. The word "traits" is choosen
over "properties" or "(data) types" to avoid confusion with the concepts of
data types and object properites from programming. A trait is almost a
property of an object in the object-oriented implementation, and it often will
conisist of one or more data types (as in strings, integers, floats, etc.)

# Abstract Base Traits

Abstract Base Traits define the "interface" of the trait system: member
functions, properties, etc. defined here must always be implemented in any
complete definition of a trait. To enforce that, the classes of this file are
python Abstract Base Classes as defined by the ABC module. Subclasses of these
classes must implement all of the methods, properties, etc., of the base class
before they can be instantated (otherwise an exception is thrown).

# Subclassing Abstract Base Traits

It is not necessarily the best to directly subclass these classes...

# About ABC

This module makes use of Python's [ABC (Abstract Base Class) library
module](https://docs.python.org/3/library/abc.html). An example and
explaination of this module is here: 

https://dbader.org/blog/abstract-base-classes-in-python

"""

from abc import ABC


class AbstractBaseTrait(ABC):
    @property
    def value(self):
        raise NotImplementedError

    @property
    def description(self):
        raise NotImplementedError

    @property
    def data_type(self):
        raise NotImplementedError

    @property
    def reference(self):
        raise NotImplementedError


class AbstractNumericTrait(AbstractBaseTrait):
    @property
    def variance(self):
        raise NotImplementedError
    @property
    def unit(self):
        raise NotImplementedError


class AbstractBaseArrayTrait(AbstractBaseTrait):
    @property
    def shape(self):
        raise NotImplementedError


class AbstractMeasurement(AbstractNumericTrait):
    @property
    def epoch(self):
        raise NotImplementedError
    @property
    def instrument(self):
        raise NotImplementedError


class AbstractBaseClassification(AbstractBaseTrait):
    @property
    def valid_classifications(self):
        raise NotImplementedError


class Base1DTrait(AbstractBaseArrayTrait): pass


class Base2DTrait(AbstractBaseArrayTrait): pass


class Base3DTrait(AbstractBaseArrayTrait): pass



