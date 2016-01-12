from collections import OrderedDict, namedtuple

from django.conf.urls import url
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import NoReverseMatch

from rest_framework.routers import SimpleRouter, DefaultRouter
from rest_framework import views
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_extensions.routers import NestedRouterMixin



class ExtendDefaultRouter(SimpleRouter):
    """
    The default router extends the SimpleRouter, but also adds in a default
    API root view, and adds format suffix patterns to the URLs.
    """
    include_root_view = True
    include_format_suffixes = True
    root_view_name = 'api-root'

    def get_api_root_view(self):
        """
        Return a view to use as the API root.
        """
        api_root_dict = OrderedDict()
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        class APIRoot(views.APIView):
            _ignore_model_permissions = True

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

        return APIRoot.as_view()

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



class ExtendNestedRouter(NestedRouterMixin, SimpleRouter):
    """
    The default router extends the SimpleRouter, but also adds in a default
    API root view, and adds format suffix patterns to the URLs.
    """
