from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse


class SampleAttributesMixin(serializers.Serializer):
    """ Mixin providing sample and data release info """

    sample = serializers.SerializerMethodField()
    data_release = serializers.SerializerMethodField()

    def get_sample(self, obj):
        return self.context['sample']

    def get_data_release(self, obj):
        return 1.0


class AstronomicalObjectAttributesMixin(SampleAttributesMixin):
    """ Mixin providing current astroobject """

    astro_object = serializers.SerializerMethodField()

    def get_astro_object(self, obj):
        return self.context['astro_object']


class TraitAttributesMixin(AstronomicalObjectAttributesMixin):
    """ Adds in survey, astro_object, trait attributes to each view"""

    branch = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()
    all_branches_versions = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    pretty_name = serializers.SerializerMethodField()
    documentation = serializers.SerializerMethodField()

    def get_branch(self, trait):
        if trait.branch is None:
            return 'None'
        else:
            return trait.branch

    def get_version(self, trait):
        if trait.version is None:
            return 'None'
        return trait.version

    def get_all_branches_versions(self, trait):
        b_v_arr = []
        branches = {}
        url_kwargs = {
            'astroobject_pk': self.context['astro_object'],
            'sample_pk': self.context['sample']
        }
        # url = reverse("data_browser:astroobject-list", kwargs=url_kwargs, request=self.context['request'])
        # removing request also removes the protocol etc.
        url = reverse("data_browser:astroobject-list", kwargs=url_kwargs)

        # trait.branches_versions.get_pretty_name(branch_name)

        for i in trait.get_all_branches_versions():
            # if i.branch != None:

            branches[str(i.branch)] = {
                "pretty_name": "tbd",
                # "pretty_name":trait.branches_versions.get_pretty_name(str(i.branch)),
                # "description":trait.branches_versions.get_description(str(i.branch)),
                "description": "",
                "versions": i.version
            }

            # Construct URL
            this_url = url + str(i.trait_name) + ':' + str(i.branch)

            # If already in array, append a version to that branch
            for j in b_v_arr:
                if j['branch'] == str(i.branch):
                    j['versions'].append(str.i.version)
            # Else add new branch
            b_v_arr.append({"branch": str(i.branch), "url": this_url,
                            "versions": [str(i.version)]})
        # print(branches)
        # print(b_v_arr)
        return b_v_arr

    def get_description(self, trait):
        return trait.get_description()

    def get_pretty_name(self, trait):
        return trait.get_pretty_name()

    def get_documentation(self, trait):
        # If API - return pre-formatted html, and replace $ with $$ for MathJax

        if self.context['request'].accepted_renderer.format == 'api' or 'html':
            if trait.get_documentation() is not None:
                # return trait.get_documentation('html').replace("$", "$$")
                return trait.get_documentation('html')
            else:
                return trait.get_documentation('html')
        else:
            return trait.get_documentation()
