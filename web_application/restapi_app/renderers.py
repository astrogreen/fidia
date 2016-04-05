from io import BytesIO
import logging
from django.template import Context, RequestContext, Template, loader
from rest_framework import VERSION, exceptions, serializers, status
from rest_framework import renderers
from rest_framework.exceptions import UnsupportedMediaType
from rest_framework.request import is_form_media_type, override_method
from django import forms
from django.core.paginator import Page
from django.template import Context, RequestContext, Template, loader
from rest_framework import VERSION, exceptions, serializers, status
from rest_framework.exceptions import ParseError
from rest_framework.request import is_form_media_type, override_method
from rest_framework.settings import api_settings
# from rest_framework.utils.breadcrumbs import get_breadcrumbs
from .utils.breadcrumbs import get_breadcrumbs_by_viewname, get_object_name
from django.core.urlresolvers import resolve
from fidia.traits.base_traits import Trait

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class FITSRenderer(renderers.BaseRenderer):
    media_type = "application/fits"
    format = "fits"
    charset = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        log.debug("Render response: %s" % renderer_context['response'])
        trait = data.serializer.instance
        if not isinstance(trait, Trait):
            raise UnsupportedMediaType("Renderer doesn't support anything but Traits!")

        byte_file = BytesIO()

        trait.as_fits(byte_file)

        return byte_file.getvalue()


class ExtendBrowsableAPIRenderer(renderers.BrowsableAPIRenderer):
    """
    Extends Browsable API to override breadcrumbs method and
    add in get_astroobj name
    """

    def get_astro_object_name(self, request):
        """
        Return the astro object name
        """
        pass
        # try:
        #     (view, unused_args, unused_kwargs) = resolve(request.path)
        # except Exception:
        #     pass
        # else:
        print(request)
        print(request.path)
        return get_object_name(request.path, request)

    def get_breadcrumbs(self, request):
        return get_breadcrumbs_by_viewname(request.path, request)

    def get_context(self, data, accepted_media_type, renderer_context):
        """
        Returns the context used to render.
        """
        view = renderer_context['view']
        request = renderer_context['request']
        response = renderer_context['response']

        renderer = self.get_default_renderer(view)

        raw_data_post_form = self.get_raw_data_form(data, view, 'POST', request)
        raw_data_put_form = self.get_raw_data_form(data, view, 'PUT', request)
        raw_data_patch_form = self.get_raw_data_form(data, view, 'PATCH', request)
        raw_data_put_or_patch_form = raw_data_put_form or raw_data_patch_form

        response_headers = dict(response.items())
        renderer_content_type = ''
        if renderer:
            renderer_content_type = '%s' % renderer.media_type
            if renderer.charset:
                renderer_content_type += ' ;%s' % renderer.charset
        response_headers['Content-Type'] = renderer_content_type

        if getattr(view, 'paginator', None) and view.paginator.display_page_controls:
            paginator = view.paginator
        else:
            paginator = None

        context = {
            'content': self.get_content(renderer, data, accepted_media_type, renderer_context),
            'view': view,
            'request': request,
            'response': response,
            'description': self.get_description(view, response.status_code),
            'name': self.get_name(view),
            'objname': self.get_astro_object_name(request),
            'version': VERSION,
            'paginator': paginator,
            'breadcrumblist': self.get_breadcrumbs(request),
            'allowed_methods': view.allowed_methods,
            'available_formats': [renderer_cls.format for renderer_cls in view.renderer_classes],
            'response_headers': response_headers,

            'put_form': self.get_rendered_html_form(data, view, 'PUT', request),
            'post_form': self.get_rendered_html_form(data, view, 'POST', request),
            'delete_form': self.get_rendered_html_form(data, view, 'DELETE', request),
            'options_form': self.get_rendered_html_form(data, view, 'OPTIONS', request),

            'filter_form': self.get_filter_form(data, view, request),

            'raw_data_put_form': raw_data_put_form,
            'raw_data_post_form': raw_data_post_form,
            'raw_data_patch_form': raw_data_patch_form,
            'raw_data_put_or_patch_form': raw_data_put_or_patch_form,

            'display_edit_forms': bool(response.status_code != 403),

            'api_settings': api_settings
        }
        return context


class SampleRenderer(ExtendBrowsableAPIRenderer):
    """
    SampleViewSet (list only)
    """
    template = 'restapi_app/sample/list-sample.html'


# class SAMIRenderer(ExtendBrowsableAPIRenderer):
#     """
#     SampleViewSet (list only)
#     """
#     template = 'restapi_app/sample/list-sample.html'
#
#
class GAMARenderer(ExtendBrowsableAPIRenderer):
    """
    SampleViewSet (list only)
    """
    template = 'restapi_app/sample/inprogress.html'


class AstroObjectRenderer(ExtendBrowsableAPIRenderer):
    """
    AstroObjectViewSet (list only)
    """
    template = 'restapi_app/sample/list-astroobject.html'


class TraitRenderer(ExtendBrowsableAPIRenderer):
    template = 'restapi_app/sample/list-trait.html'


class TraitPropertyRenderer(ExtendBrowsableAPIRenderer):
    pass


class QueryRenderer(ExtendBrowsableAPIRenderer):
    """
    BrowseSurveysViewSet
    """
    # note this template extends restapi_app/query/query.html
    # where most of the html structure resides
    template = 'restapi_app/query/query-builder-module.html'


class SOVListRenderer(ExtendBrowsableAPIRenderer):
    """
    BrowseSurveysViewSet
    """

    template = 'restapi_app/sov/list.html'


class SOVDetailRenderer(ExtendBrowsableAPIRenderer):
    """
    BrowseSurveysViewSet
    """

    template = 'restapi_app/sov/detail.html'


class RegisterRenderer(ExtendBrowsableAPIRenderer):
    """
    BrowseSurveysViewSet
    """
    template = 'restapi_app/register/register.html'


class APIRootRenderer(ExtendBrowsableAPIRenderer):
    """
    APIROOT Template
    """
    template = 'restapi_app/api-root/list.html'