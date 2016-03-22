from io import BytesIO
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
from .utils.breadcrumbs import get_breadcrumbs_by_viewname, get_breadcrumbs_by_id

from fidia.traits.base_traits import Trait


class FITSRenderer(renderers.BaseRenderer):
    media_type = "application/fits"
    format = "fits"
    charset = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        trait = data.serializer.instance
        if not isinstance(trait, Trait):
            raise UnsupportedMediaType("Renderer doesn't support anything but Traits!")

        byte_file = BytesIO()

        trait.as_fits(byte_file)

        return byte_file.getvalue()



class ListNoDetailRenderer(renderers.BaseRenderer):
    """
    Use this as a parent class for all asvo sample/galaxy/trait/traitproperty
    end points. Custom get_breadcrumbs method (removes the 'list/detail attributes')

    """
    template = 'rest_framework/api.html'
    media_type = 'text/html'
    format = 'api'
    filter_template = 'rest_framework/filters/base.html'
    charset = 'utf-8'
    form_renderer_class = renderers.HTMLFormRenderer
    def get_default_renderer(self, view):
        """
        Return an instance of the first valid renderer.
        (Don't use another documenting renderer.)
        """
        renderers = [renderer for renderer in view.renderer_classes
                     if not issubclass(renderer, ListNoDetailRenderer)]
        non_template_renderers = [renderer for renderer in renderers
                                  if not hasattr(renderer, 'get_template_names')]

        if not renderers:
            return None
        elif non_template_renderers:
            return non_template_renderers[0]()
        return renderers[0]()

    def get_content(self, renderer, data,
                    accepted_media_type, renderer_context):
        """
        Get the content as if it had been rendered by the default
        non-documenting renderer.
        """
        if not renderer:
            return '[No renderers were found]'

        renderer_context['indent'] = 4
        content = renderer.render(data, accepted_media_type, renderer_context)

        render_style = getattr(renderer, 'render_style', 'text')
        assert render_style in ['text', 'binary'], 'Expected .render_style ' \
            '"text" or "binary", but got "%s"' % render_style
        if render_style == 'binary':
            return '[%d bytes of binary content]' % len(content)

        return content

    def show_form_for_method(self, view, method, request, obj):
        """
        Returns True if a form should be shown for this method.
        """
        if method not in view.allowed_methods:
            return  # Not a valid method

        try:
            view.check_permissions(request)
            if obj is not None:
                view.check_object_permissions(request, obj)
        except exceptions.APIException:
            return False  # Doesn't have permissions
        return True

    def _get_serializer(self, serializer_class, view_instance, request, *args, **kwargs):
        kwargs['context'] = {
            'request': request,
            'format': self.format,
            'view': view_instance
        }
        return serializer_class(*args, **kwargs)

    def get_rendered_html_form(self, data, view, method, request):
        """
        Return a string representing a rendered HTML form, possibly bound to
        either the input or output data.

        In the absence of the View having an associated form then return None.
        """
        # See issue #2089 for refactoring this.
        serializer = getattr(data, 'serializer', None)
        if serializer and not getattr(serializer, 'many', False):
            instance = getattr(serializer, 'instance', None)
            if isinstance(instance, Page):
                instance = None
        else:
            instance = None

        # If this is valid serializer data, and the form is for the same
        # HTTP method as was used in the request then use the existing
        # serializer instance, rather than dynamically creating a new one.
        if request.method == method and serializer is not None:
            try:
                kwargs = {'data': request.data}
            except ParseError:
                kwargs = {}
            existing_serializer = serializer
        else:
            kwargs = {}
            existing_serializer = None

        with override_method(view, request, method) as request:
            if not self.show_form_for_method(view, method, request, instance):
                return

            if method in ('DELETE', 'OPTIONS'):
                return True  # Don't actually need to return a form

            has_serializer = getattr(view, 'get_serializer', None)
            has_serializer_class = getattr(view, 'serializer_class', None)

            if (
                (not has_serializer and not has_serializer_class) or
                not any(is_form_media_type(parser.media_type) for parser in view.parser_classes)
            ):
                return

            if existing_serializer is not None:
                serializer = existing_serializer
            else:
                if has_serializer:
                    if method in ('PUT', 'PATCH'):
                        serializer = view.get_serializer(instance=instance, **kwargs)
                    else:
                        serializer = view.get_serializer(**kwargs)
                else:
                    # at this point we must have a serializer_class
                    if method in ('PUT', 'PATCH'):
                        serializer = self._get_serializer(view.serializer_class, view,
                                                          request, instance=instance, **kwargs)
                    else:
                        serializer = self._get_serializer(view.serializer_class, view,
                                                          request, **kwargs)

            if hasattr(serializer, 'initial_data'):
                serializer.is_valid()

            form_renderer = self.form_renderer_class()
            return form_renderer.render(
                serializer.data,
                self.accepted_media_type,
                {'style': {'template_pack': 'rest_framework/horizontal'}}
            )

    def get_raw_data_form(self, data, view, method, request):
        """
        Returns a form that allows for arbitrary content types to be tunneled
        via standard HTML forms.
        (Which are typically application/x-www-form-urlencoded)
        """
        # See issue #2089 for refactoring this.
        serializer = getattr(data, 'serializer', None)
        if serializer and not getattr(serializer, 'many', False):
            instance = getattr(serializer, 'instance', None)
            if isinstance(instance, Page):
                instance = None
        else:
            instance = None

        with override_method(view, request, method) as request:
            # Check permissions
            if not self.show_form_for_method(view, method, request, instance):
                return

            # If possible, serialize the initial content for the generic form
            default_parser = view.parser_classes[0]
            renderer_class = getattr(default_parser, 'renderer_class', None)
            if (hasattr(view, 'get_serializer') and renderer_class):
                # View has a serializer defined and parser class has a
                # corresponding renderer that can be used to render the data.

                if method in ('PUT', 'PATCH'):
                    serializer = view.get_serializer(instance=instance)
                else:
                    serializer = view.get_serializer()

                # Render the raw data content
                renderer = renderer_class()
                accepted = self.accepted_media_type
                context = self.renderer_context.copy()
                context['indent'] = 4
                content = renderer.render(serializer.data, accepted, context)
            else:
                content = None

            # Generate a generic form that includes a content type field,
            # and a content field.
            media_types = [parser.media_type for parser in view.parser_classes]
            choices = [(media_type, media_type) for media_type in media_types]
            initial = media_types[0]

            class GenericContentForm(forms.Form):
                _content_type = forms.ChoiceField(
                    label='Media type',
                    choices=choices,
                    initial=initial,
                    widget=forms.Select(attrs={'data-override': 'content-type'})
                )
                _content = forms.CharField(
                    label='Content',
                    widget=forms.Textarea(attrs={'data-override': 'content'}),
                    initial=content
                )

            return GenericContentForm()

    def get_name(self, view):
        return view.get_view_name()

    def get_astro_object_name(self, request):
        """
        Return the astro object name
        """
        if 'galaxy_pk' in request.kwargs:
            return request.kwargs['galaxy_pk']
        else:
            pass

    def get_description(self, view, status_code):
        if status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            return ''
        return view.get_view_description(html=True)

    def get_breadcrumbs_by_viewname(self, request):
        return get_breadcrumbs_by_viewname(request.path, request)

    def get_breadcrumbs_by_id(self, request):
        return get_breadcrumbs_by_id(request.path, request)

    def get_filter_form(self, data, view, request):
        if not hasattr(view, 'get_queryset') or not hasattr(view, 'filter_backends'):
            return

        # Infer if this is a list view or not.
        paginator = getattr(view, 'paginator', None)
        if isinstance(data, list):
            pass
        elif (paginator is not None and data is not None):
            try:
                paginator.get_results(data)
            except (TypeError, KeyError):
                return
        elif not isinstance(data, list):
            return

        queryset = view.get_queryset()
        elements = []
        for backend in view.filter_backends:
            if hasattr(backend, 'to_html'):
                html = backend().to_html(request, queryset, view)
                if html:
                    elements.append(html)

        if not elements:
            return

        template = loader.get_template(self.filter_template)
        context = Context({'elements': elements})
        return template.render(context)

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
            'objname': self.get_astro_object_name(view),
            'version': VERSION,
            'paginator': paginator,
            'breadcrumblist': self.get_breadcrumbs_by_id(request),
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

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render the HTML for the browsable API representation.
        """
        self.accepted_media_type = accepted_media_type or ''
        self.renderer_context = renderer_context or {}

        template = loader.get_template(self.template)
        context = self.get_context(data, accepted_media_type, renderer_context)
        context = RequestContext(renderer_context['request'], context)
        ret = template.render(context)

        # Munge DELETE Response code to allow us to return content
        # (Do this *after* we've rendered the template so that we include
        # the normal deletion response code in the output)
        response = renderer_context['response']
        if response.status_code == status.HTTP_204_NO_CONTENT:
            response.status_code = status.HTTP_200_OK

        return ret
    #
    #
    # def get_default_renderer(self, view):
    #     """
    #     Return an instance of the first valid renderer.
    #     (Don't use another documenting renderer.)
    #     """
    #     renderers = [renderer for renderer in view.renderer_classes
    #                  if not issubclass(renderer, SOVRenderer)]
    #     non_template_renderers = [renderer for renderer in renderers
    #                               if not hasattr(renderer, 'get_template_names')]
    #
    #     if not renderers:
    #         return None
    #     elif non_template_renderers:
    #         return non_template_renderers[0]()
    #     return renderers[0]()
    #
    # def get_content(self, renderer, data,
    #                 accepted_media_type, renderer_context):
    #     """
    #     Get the content as if it had been rendered by the default
    #     non-documenting renderer.
    #     """
    #     if not renderer:
    #         return '[No renderers were found]'
    #
    #     renderer_context['indent'] = 4
    #     content = renderer.render(data, accepted_media_type, renderer_context)
    #
    #     render_style = getattr(renderer, 'render_style', 'text')
    #     assert render_style in ['text', 'binary'], 'Expected .render_style ' \
    #         '"text" or "binary", but got "%s"' % render_style
    #     if render_style == 'binary':
    #         return '[%d bytes of binary content]' % len(content)
    #
    #     return content
    #
    # def _get_serializer(self, serializer_class, view_instance, request, *args, **kwargs):
    #     kwargs['context'] = {
    #         'request': request,
    #         'format': self.format,
    #         'view': view_instance
    #     }
    #     return serializer_class(*args, **kwargs)
    #
    # def get_name(self, view):
    #     return view.get_view_name()
    #
    # def get_description(self, view, status_code):
    #     if status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
    #         return ''
    #     return view.get_view_description(html=True)
    #
    # def get_breadcrumbs(self, request):
    #     return get_breadcrumbs(request.path, request)
    #
    # def get_filter_form(self, data, view, request):
    #     if not hasattr(view, 'get_queryset') or not hasattr(view, 'filter_backends'):
    #         return
    #
    #     # Infer if this is a list view or not.
    #     paginator = getattr(view, 'paginator', None)
    #     if isinstance(data, list):
    #         pass
    #     elif (paginator is not None and data is not None):
    #         try:
    #             paginator.get_results(data)
    #         except (TypeError, KeyError):
    #             return
    #     elif not isinstance(data, list):
    #         return
    #
    #     queryset = view.get_queryset()
    #     elements = []
    #     for backend in view.filter_backends:
    #         if hasattr(backend, 'to_html'):
    #             html = backend().to_html(request, queryset, view)
    #             if html:
    #                 elements.append(html)
    #
    #     if not elements:
    #         return
    #
    #     template = loader.get_template(self.filter_template)
    #     context = Context({'elements': elements})
    #     return template.render(context)
    #
    # def get_context(self, data, accepted_media_type, renderer_context):
    #     """
    #     Returns the context used to render.
    #     """
    #     view = renderer_context['view']
    #     request = renderer_context['request']
    #     response = renderer_context['response']
    #
    #     renderer = self.get_default_renderer(view)
    #
    #     response_headers = dict(response.items())
    #     renderer_content_type = ''
    #     if renderer:
    #         renderer_content_type = '%s' % renderer.media_type
    #         if renderer.charset:
    #             renderer_content_type += ' ;%s' % renderer.charset
    #     response_headers['Content-Type'] = renderer_content_type
    #
    #     if getattr(view, 'paginator', None) and view.paginator.display_page_controls:
    #         paginator = view.paginator
    #     else:
    #         paginator = None
    #
    #     context = {
    #         'content': self.get_content(renderer, data, accepted_media_type, renderer_context),
    #         'view': view,
    #         'request': request,
    #         'response': response,
    #         'description': self.get_description(view, response.status_code),
    #         'name': self.get_name(view),
    #         'version': VERSION,
    #         'paginator': paginator,
    #         'breadcrumblist': self.get_breadcrumbs(request),
    #         'allowed_methods': view.allowed_methods,
    #         'available_formats': [renderer_cls.format for renderer_cls in view.renderer_classes],
    #         'response_headers': response_headers,
    #
    #         'filter_form': self.get_filter_form(data, view, request),
    #
    #         'display_edit_forms': bool(response.status_code != 403),
    #
    #         'api_settings': api_settings
    #     }
    #     return context
    #
    # def render(self, data, accepted_media_type=None, renderer_context=None):
    #     """
    #     Render the HTML for the browsable API representation.
    #     """
    #     self.accepted_media_type = accepted_media_type or ''
    #     self.renderer_context = renderer_context or {}
    #
    #     template = loader.get_template(self.template)
    #     context = self.get_context(data, accepted_media_type, renderer_context)
    #     context = RequestContext(renderer_context['request'], context)
    #     ret = template.render(context)
    #
    #     # Munge DELETE Response code to allow us to return content
    #     # (Do this *after* we've rendered the template so that we include
    #     # the normal deletion response code in the output)
    #     response = renderer_context['response']
    #     if response.status_code == status.HTTP_204_NO_CONTENT:
    #         response.status_code = status.HTTP_200_OK
    #
    #     return ret

class SampleRenderer(renderers.BrowsableAPIRenderer):
    """
    SampleViewSet (list only)
    """
    template = 'restapi_app/browse/list-sample.html'


class AstroObjectRenderer(renderers.BrowsableAPIRenderer):
    """
    AstroObjectViewSet (list only)
    """
    template = 'restapi_app/browse/list-astroobject.html'


class QueryRenderer(renderers.BrowsableAPIRenderer):
    """
    BrowseSurveysViewSet
    """
    # note this template extends restapi_app/query/query.html
    # where most of the html structure resides
    template = 'restapi_app/query/query-builder-module.html'


class SOVListRenderer(renderers.BrowsableAPIRenderer):
    """
    BrowseSurveysViewSet
    """

    template = 'restapi_app/sov/list.html'


class SOVDetailRenderer(renderers.BrowsableAPIRenderer):
    """
    BrowseSurveysViewSet
    """

    template = 'restapi_app/sov/detail.html'

