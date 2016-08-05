from __future__ import unicode_literals

from django.core.urlresolvers import get_script_prefix, resolve

from restapi_app.utils.helpers import run_once

def get_object_name(url, request=None):

    from django.utils.html import escape
    # change for query-detail, galaxy-list and trait-list
    name_space = escape(resolve(url).url_name)
    name = ''
    if name_space == 'query-list':
        name = 'Query History'
    if request.parser_context['kwargs']:
        if 'pk' in request.parser_context['kwargs']:
            if name_space == 'query-detail':
                pk = request.parser_context['kwargs']['pk']
                name = pk
            if name_space == 'sov-detail':
                pk = request.parser_context['kwargs']['pk']
                name = pk
        elif 'galaxy_pk' in request.parser_context['kwargs']:
            if name_space == 'galaxy-list':
                galaxy_pk = request.parser_context['kwargs']['galaxy_pk']
                name = galaxy_pk
            if name_space == 'trait-list':
                # format to human readable
                trait_pk = request.parser_context['kwargs']['trait_pk'].split("_")
                # .title capitalizes the first letter of every word in words list
                name = (" ".join(trait_pk)).title()
            if name_space == 'traitproperty-list':
                traitproperty_pk = request.parser_context['kwargs']['traitproperty_pk'].split("_")
                name = (" ".join(traitproperty_pk)).title()

    if name_space == 'gama-list':
        name = 'gama'
    elif name_space == 'sami-list':
        name = 'sami'
    elif name_space == 'sov-list':
        name = 'SOV'

    return name


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

    # The breadcrumb list will override the view name from the last array to the first
    try:
        (view, unused_args, unused_kwargs) = resolve(url)
    except Exception:
        pass
    else:
        cls = getattr(view, 'cls', None)
        breadcrumb_list_from_view = []
        if hasattr(cls, 'breadcrumb_list'):
            assert isinstance(cls.breadcrumb_list, list)
            breadcrumb_list_from_view = cls.breadcrumb_list

    def breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen, breadcrumb_list_from_view):
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
                    # PREVENT 'list' or 'detail' being appended
                    # suffix = getattr(view, 'suffix', None)
                    suffix = ''
                    name = view_name_func(cls, suffix)
                    print(name)
                    # new_name = get_object_name(url, request)

                    # if new_name != '':
                    #     name = new_name

                    if breadcrumb_list_from_view:
                        if breadcrumb_list_from_view.__len__() > 0:
                            name = breadcrumb_list_from_view.pop()
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
            return breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen, breadcrumb_list_from_view)

        # Drop trailing non-slash off the end and continue to try to
        # resolve more breadcrumbs
        url = url[:url.rfind('/') + 1]
        return breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen, breadcrumb_list_from_view)

    prefix = get_script_prefix().rstrip('/')
    url = url[len(prefix):]
    return breadcrumbs_recursive(url, [], prefix, [], breadcrumb_list_from_view)








