import pytest

from fidia.descriptions import *

class TestDescriptions:

    @pytest.fixture
    def class_with_descriptions(self):
        class KlassWithDescriptions:
            description = Description()
            documentation = Documentation()
            pretty_name = PrettyName()

        return KlassWithDescriptions

    @pytest.fixture
    def sub_class_with_descriptions(self, class_with_descriptions):
        class SubKlassWithDescriptions(class_with_descriptions):
            pass

        return SubKlassWithDescriptions

    def test_subclass_has_descriptions(self, sub_class_with_descriptions):
        klass = sub_class_with_descriptions()

        assert klass.description is None

        assert klass.documentation is None

    def test_klass_descriptions_not_polluted(self):

        class A:
            description = Description()
            documentation = Documentation()
            pretty_name = PrettyName()

        a1 = A()
        a1.description = "A1desc"

        assert a1.description == "A1desc"

        a2 = A()
        assert a2.description is None
        a2.description = "A2desc"
        assert a2.description == "A2desc"
        assert a1.description == "A1desc"

    def test_description_inheritance(self, class_with_descriptions):

        klass = class_with_descriptions()

        class SubKlass(class_with_descriptions):
            pass

        SubKlass.documentation = "MyDocKlass"

        subklass = SubKlass()
        subklass2 = SubKlass()

        subklass.documentation = "MyDoc"

        assert subklass.documentation == "MyDoc"
        assert klass.documentation is None

        assert subklass2.documentation == "MyDocKlass"
        # print(class_with_descriptions.documentation)
        # assert class_with_descriptions.documentation is None

        assert class_with_descriptions().documentation is None