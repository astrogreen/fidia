from rest_framework.reverse import reverse
from pprint import pprint

class TraitHelper:
    """ Returns all the useful information about this particular trait """

    def __init__(self, *args, **kwargs):
        self.fidia_type = self.survey = self.astro_object = self.trait = self.trait_key = \
            self.branch = self.version = self.trait_type = self.trait_class = self.trait_name = \
            self.trait_url = self.trait_pretty_name = self.default_trait_key = self.subtrait_pretty_name = self.sub_trait = ''
        self.all_branches_versions = self.trait_registry = {}
        self.sub_traits = self.sub_trait_list = self.formats = self.breadcrumb_list = []
        self.trait_2D_map = False

    def set_attributes(self, survey_pk=None, astroobject_pk=None, trait_pk=None, trait=None, ar=None):
        # Dict of available traits
        self.trait_registry = ar.available_traits
        self.default_trait_key = self.trait_registry.update_key_with_defaults(trait_pk)
        self.trait_class = self.trait_registry.retrieve_with_key(self.default_trait_key)

        self.survey = survey_pk
        self.astro_object = astroobject_pk
        self.trait = trait_pk

        self.trait_type = trait.trait_type
        self.trait_name = str(trait.trait_name)
        self.trait_key = self.default_trait_key

        self.trait_pretty_name = trait.get_pretty_name()
        self.branch = trait.branch
        self.version = trait.version
        self.formats = self.trait_class.get_available_export_formats()
        self.sub_traits = [sub_trait.trait_name for sub_trait in trait.get_all_subtraits()]
        self.trait_url = reverse("sov:trait-list",
                                 kwargs={'survey_pk': survey_pk, 'astroobject_pk': astroobject_pk,
                                         'trait_pk': trait_pk, })

        # - Branches -
        # removing request from reverse also removes the protocol etc.
        astro_object_url = reverse("sov:astroobject-list",
                                   kwargs={'astroobject_pk': astroobject_pk, 'survey_pk': survey_pk})

        self.all_branches_versions = {}

        for tk in self.trait_registry.get_all_traitkeys(trait_name_filter=trait.trait_name):

            # trait_class for trait_key
            tc = self.trait_registry.retrieve_with_key(tk)

            if str(tk.branch) in self.all_branches_versions:
                # if this branch already exists, append the new version
                self.all_branches_versions[str(tk.branch)]["versions"].append(str(tk.version))
            else:
                self.all_branches_versions[str(tk.branch)] = {
                    "description": tc.branches_versions.get_description(tk.branch),
                    "pretty_name": tc.branches_versions.get_pretty_name(tk.branch),
                    "url": astro_object_url + str(trait.trait_name) + ':' + str(tk.branch),
                    "versions": [str(tk.version)]
                }
