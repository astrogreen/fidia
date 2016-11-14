import pytest

from fidia.descriptions import *


class KlassWithDescriptions(DescriptionsMixin):
    """Classification of emission in each spaxel as star forming or as other ionisation mechanisms.

    We classify each spaxel using (when possible) [OIII]/Hβ, [NII]/Hα,
    [SII]/Hα, and [OI]/Hα flux ratios from EmissionLineFitsV01 to
    determine whether the emission lines are dominated by photoionization from
    HII regions or other sources like AGN or shocks, using the BPT/VO87
    diagnostic diagrams and dividing lines from Kewley et al. 2006.  We only
    classify spaxels with ratios that have a signal-to-noise ratio of at least
    5.

    We additionally add a likely classification of "star-forming" to spaxels
    with $\log({\rm [NII]}/{\rm Hα}) <-0.4 $ without an [OIII] detection.

    Classifications are stored in the map as an integer with the following definitions:

    | Pixel Value | Classification |
    | ------------|----------------|
    |   0         |  No data       |
    |   1         | star formation dominates the emission in all available line ratios |
    |   2         | other ionization mechanisms dominate |

    We note that these classifications are done only using the TOTAL EMISSION
    LINE FLUX in a spectrum.  Thus, for spectra which contain 2 or 3 components,
    we classify the total emission in that spaxel, not the individual
    components.

    """

    descriptions_allowed = 'class'


KlassWithDescriptions.set_pretty_name('KlassName')

class TestDescriptions:

    @pytest.fixture
    def class_with_descriptions(self):

        return KlassWithDescriptions

    @pytest.fixture
    def sub_class_with_descriptions(self, class_with_descriptions):
        class SubKlassWithDescriptions(class_with_descriptions):
            pass

        return SubKlassWithDescriptions
    #
    # def test_subclass_has_descriptions(self, sub_class_with_descriptions):
    #     klass = sub_class_with_descriptions()  # type: SubKlassWithDescriptions
    #
    #     assert klass.get_description
    #
    #     assert klass.documentation is None
    #
    # def test_klass_descriptions_not_polluted(self):
    #
    #     class A:
    #         description = Description()
    #         documentation = Documentation()
    #         pretty_name = PrettyName()
    #
    #     a1 = A()
    #     a1.description = "A1desc"
    #
    #     assert a1.description == "A1desc"
    #
    #     a2 = A()
    #     assert a2.description is None
    #     a2.description = "A2desc"
    #     assert a2.description == "A2desc"
    #     assert a1.description == "A1desc"
    #
    # def test_description_inheritance(self, class_with_descriptions):
    #
    #     klass = class_with_descriptions()
    #
    #     class SubKlass(class_with_descriptions):
    #         pass
    #
    #     SubKlass.documentation = "MyDocKlass"
    #
    #     subklass = SubKlass()
    #     subklass2 = SubKlass()
    #
    #     subklass.documentation = "MyDoc"
    #
    #     assert subklass.documentation == "MyDoc"
    #     assert klass.documentation is None
    #
    #     assert subklass2.documentation == "MyDocKlass"
    #     # print(class_with_descriptions.documentation)
    #     # assert class_with_descriptions.documentation is None
    #
    #     assert class_with_descriptions().documentation is None

    def test_doc_string_deindent(self, class_with_descriptions):
        class IndentDescriptionTest(DescriptionsMixin):
            r"""Classification of emission in each spaxel as star forming or as other ionisation mechanisms.

            We classify each spaxel using (when possible) [OIII]/Hβ, [NII]/Hα,
            [SII]/Hα, and [OI]/Hα flux ratios from EmissionLineFitsV01 to
            determine whether the emission lines are dominated by photoionization from
            HII regions or other sources like AGN or shocks, using the BPT/VO87
            diagnostic diagrams and dividing lines from Kewley et al. 2006.  We only
            classify spaxels with ratios that have a signal-to-noise ratio of at least
            5.

            We additionally add a likely classification of "star-forming" to spaxels
            with $\log({\rm [NII]}/{\rm Hα}) <-0.4 $ without an [OIII] detection.
            """

            descriptions_allowed = 'class'



        doc = IndentDescriptionTest.get_documentation()

        split_doc = doc.splitlines()

        assert split_doc[2].startswith("We classify")

    def test_description_removed_from_documentation_docstring(self):

        class KlassWithDescription(DescriptionsMixin):
            """The Description.

            The documentation. And More!"""

        assert KlassWithDescription.get_documentation().startswith("The documentation")

    def test_multiline_description_from_docstring(self):

        class KlassWithDescription(DescriptionsMixin):
            """A very long description in a doc-string that happens to span
            multiple lines because it has been wrapped in the original
            sourcecode.

            This kind of thing should be avoided!"""

        print(KlassWithDescription.get_description())

        assert KlassWithDescription.get_description() == "A very long description in a doc-string that happens to " \
                                                         "span multiple lines because it has been wrapped in the " \
                                                         "original sourcecode."
