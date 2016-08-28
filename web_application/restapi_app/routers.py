from collections import OrderedDict, namedtuple

from django.conf.urls import url
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import NoReverseMatch

from rest_framework.routers import SimpleRouter, DefaultRouter
from rest_framework import views
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer

# from restapi_app.renderers import APIRootRenderer
from restapi_app.renderers import ExtendBrowsableAPIRenderer

class ExtendDefaultRouter(SimpleRouter):
    """
    The default router extends the SimpleRouter and overrides the SIMPLE router (does not add in a default
    API root view, and adds format suffix patterns to the URLs).

    """
    include_root_view = True
    include_format_suffixes = True
    root_view_name = 'data'

    def get_api_root_view(self):
        """
        Return a view to use as the API root.
        """
        api_root_dict = OrderedDict()
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            # DRF registers all views on the router as list even if they don't have a list action...
            # Here, exclude the query-detail view to prevent it showing in the api-root (prefix list incorrectly appended and incorrect url resolved)
            # /asvo/<var>data/query-history/	restapi_app.views.QueryListView	query-list      <-- this is the list action
            # /asvo/<var>data/query/<pk>/	restapi_app.views.QueryRetrieveUpdateDestroyView	query-detail <-- this retrieve action isn't needed (or handled properly) by the router

            if prefix == 'query' and basename == 'query':
                pass
            else:
                api_root_dict[prefix] = list_name.format(basename=basename)

        class DATA(views.APIView):
            # _ignore_model_permissions = True
            renderer_classes = [ExtendBrowsableAPIRenderer, JSONRenderer]

            def get(self, request, *args, **kwargs):
                ret = OrderedDict()
                namespace = request.resolver_match.namespace
                for key, url_name in api_root_dict.items():
                    if namespace:
                        url_name = namespace + ':' + url_name
                    try:
                        ret[key] = reverse(
                            url_name,
                            args=args,
                            kwargs=kwargs,
                            request=request,
                            format=kwargs.get('format', None)
                        )
                    except NoReverseMatch:
                        # Don't bail out if eg. no list routes exist, only detail routes.
                        continue
                return Response(ret)
        return DATA.as_view()


    def get_urls(self):
        """
        Generate the list of URL patterns, including a default root view
        for the API, and appending `.json` style format suffixes.
        """
        urls = []

        if self.include_root_view:
            root_url = url(r'^$', self.get_api_root_view(), name=self.root_view_name)
            urls.append(root_url)

        default_urls = super(ExtendDefaultRouter, self).get_urls()
        urls.extend(default_urls)

        if self.include_format_suffixes:
            urls = format_suffix_patterns(urls)

        return urls


# class NestedExtendDefaultRouter(ExtendDefaultRouter):
class NestedExtendDefaultRouter(SimpleRouter):
    def __init__(self, parent_router, parent_prefix, *args, **kwargs):
        """ Create a NestedSimpleRouter nested within `parent_router`
        Args:

        parent_router: Parent router. Mayb be a simple router or another nested
            router.

        parent_prefix: The url prefix within parent_router under which the
            routes from this router should be nested.

        lookup:
            The regex variable that matches an instance of the parent-resource
            will be called '<lookup>_<parent-viewset.lookup_field>'
            In the example above, lookup=domain and the parent viewset looks up
            on 'pk' so the parent lookup regex will be 'domain_pk'.
            Default: 'nested_<n>' where <n> is 1+parent_router.nest_count

        """
        self.parent_router = parent_router
        self.parent_prefix = parent_prefix
        self.nest_count = getattr(parent_router, 'nest_count', 0) + 1
        self.nest_prefix = kwargs.pop('lookup', 'nested_%i' % self.nest_count) + '_'
        super(NestedExtendDefaultRouter, self).__init__(*args, **kwargs)
        parent_registry = [registered for registered in self.parent_router.registry if registered[0] == self.parent_prefix]
        try:
            parent_registry = parent_registry[0]
            parent_prefix, parent_viewset, parent_basename = parent_registry
        except:
            raise RuntimeError('parent registered resource not found')

        nested_routes = []
        parent_lookup_regex = parent_router.get_lookup_regex(parent_viewset, self.nest_prefix)


        # self.parent_regex = '{parent_prefix}/{parent_lookup_regex}/'.format(
        #     parent_prefix=parent_prefix,
        #     parent_lookup_regex=parent_lookup_regex
        # )

        # Liz: Override the parent regex (removing (?P<sample_PK>[^/.+]/   )

        self.parent_regex = '{parent_prefix}/'.format(
            parent_prefix=parent_prefix,
        )
        if hasattr(parent_router, 'parent_regex'):
            self.parent_regex = parent_router.parent_regex+self.parent_regex

        for route in self.routes:
            route_contents = route._asdict()

            # This will get passed through .format in a little bit, so we need
            # to escape it
            escaped_parent_regex = self.parent_regex.replace('{', '{{').replace('}', '}}')

            route_contents['url'] = route.url.replace('^', '^'+escaped_parent_regex)
            nested_routes.append(type(route)(**route_contents))

        self.routes = nested_routes