from rest_framework.reverse import reverse

def trait_helper(self, trait, ar, survey_pk, astroobject_pk, trait_pk, request):
    """ Returns all the useful information about this particular trait """

    trait_registry = ar.available_traits
    default_trait_key = trait_registry.update_key_with_defaults(trait_pk)

    trait_info = {}

    # Branch - replace with string NONE
    if trait.branch is None:
        trait_info['branch'] = 'None'
    else:
        trait_info['branch'] = trait.branch

    if trait.version is None:
        trait_info['version'] = 'None'
    else:
        trait_info['version'] = trait.version

    trait_info['trait_key'] = trait.trait_key
    trait_info['trait_key_str'] = default_trait_key
    trait_info['description'] = trait.get_description()
    trait_info['pretty_name'] = trait.get_pretty_name()
    trait_info['trait_type'] = trait.trait_type

    # If html/browsable api - return pre-formatted html
    # REMOVED - all documentation appears in the schema browser
    # if request.accepted_renderer.format == 'api' or 'html':
    #     trait_info['documentation'] = trait.get_documentation('html')
    # else:
    #     trait_info['documentation'] = trait.get_documentation()

    b_v_arr = []
    branches = {}

    _astro_object_url = reverse("data_browser:astroobject-list", kwargs={
        'survey_pk': survey_pk,
        'astroobject_pk': astroobject_pk,
    })

    for i in trait.get_all_branches_versions():
        branches[str(i.branch)] = {
            # "pretty_name": trait.branches_versions.get_pretty_name(str(i.branch)),
            # "description": trait.branches_versions.get_description(str(i.branch)),
            "pretty_name": "branch_pretty_name",
            "description": "branch_description",
            "versions": i.version
        }

        # Construct URL
        this_url = _astro_object_url + str(i.trait_name) + ':' + str(i.branch)

        # If already in array, append a version to that branch
        for j in b_v_arr:
            if j['branch'] == str(i.branch):
                j['versions'].append(str.i.version)
        # Else add new branch
        b_v_arr.append({"branch": str(i.branch), "url": this_url,
                        "versions": [str(i.version)]})

    trait_info['all_branches_versions'] = b_v_arr

    trait_info['url'] = reverse("data_browser:trait-list", kwargs={
        'survey_pk': survey_pk,
        'astroobject_pk': astroobject_pk,
        'trait_pk': trait_pk,
    })

    return trait_info


def sub_trait_helper(self, trait, ar, sample_pk, astroobject_pk, trait_pk, request):
    return 'sub_trait_attributes will go here'