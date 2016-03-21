from __future__ import unicode_literals

from django.core.urlresolvers import get_script_prefix, resolve


def get_breadcrumbs_by_viewname(url, request=None):
    """
    Given a url returns a list of breadcrumbs, which are each a
    tuple of (name, url).

    This method doesn't append 'list' or 'detail' as for the SOV we're just using the list view
    """
    from rest_framework.reverse import preserve_builtin_query_params
    from rest_framework.settings import api_settings
    from rest_framework.views import APIView

    view_name_func = api_settings.VIEW_NAME_FUNCTION

    def breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen):
        """
        Add tuples of (name, url) to the breadcrumbs list,
        progressively chomping off parts of the url.
        """

        try:
            (view, unused_args, unused_kwargs) = resolve(url)
        except Exception:
            pass
        else:
            # Check if this is a REST framework view,
            # and if so add it to the breadcrumbs
            cls = getattr(view, 'cls', None)
            if cls is not None and issubclass(cls, APIView):
                # Don't list the same view twice in a row.
                # Probably an optional trailing slash.
                if not seen or seen[-1] != view:
                    # suffix = getattr(view, 'suffix', None)
                    # PREVENT 'list' or 'detail' being appended
                    suffix = ''
                    name = view_name_func(cls, suffix)

                    # print(name)
                    # if name == "Astro Object":
                    #     name = 'tada'
                    # override with galaxy p_K

                    insert_url = preserve_builtin_query_params(prefix + url, request)
                    breadcrumbs_list.insert(0, (name, insert_url))
                    seen.append(view)

        if url == '':
            # All done
            return breadcrumbs_list

        elif url.endswith('/'):
            # Drop trailing slash off the end and continue to try to
            # resolve more breadcrumbs
            url = url.rstrip('/')
            return breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen)

        # Drop trailing non-slash off the end and continue to try to
        # resolve more breadcrumbs
        url = url[:url.rfind('/') + 1]
        return breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen)

    prefix = get_script_prefix().rstrip('/')
    url = url[len(prefix):]
    return breadcrumbs_recursive(url, [], prefix, [])


def get_breadcrumbs_by_id(url, request=None):
    """
    crudely replaces view name for astro object using galaxy_pk
    """
    url = get_breadcrumbs_by_viewname(url, request=None)

    # def get_coords_and_switch(url, new_name):
    #     for i, l in enumerate(url):
    #         for j, m in enumerate(l):
    #             if m == "Astro Object":
    #                 # save the url before removing that
    #                 # list and appending new
    #                 # note this requires the change to be the last
    #                 # link of the endpoint i.e., /a/b/c <--- c
    #                 new_name_url = url[i][j+1]
    #                 del url[i]
    #                 url.append((new_name, new_name_url))
    #                 return url
    #
    # if request.parser_context['kwargs']['galaxy_pk']:
    #     get_coords_and_switch(url, request.parser_context['kwargs']['galaxy_pk'])

    return url





