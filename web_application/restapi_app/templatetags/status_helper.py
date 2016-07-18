from __future__ import unicode_literals, absolute_import
from django.utils.html import escape, format_html
from django.utils.safestring import SafeData, mark_safe
from django import template

from rest_framework import status

import restapi_app.templatetags.internal_extras


register = template.Library()


@register.simple_tag
def is_informational(status_code):
    if status.is_informational(status_code):
        return True
    else:
        return False


@register.simple_tag
def is_success(status_code):
    status_code=int(status_code)
    if status.is_success(status_code):
        return True
    else:
        return False


@register.simple_tag
def is_redirect(status_code):
    if status.is_redirect(status_code):
        return True
    else:
        return False

@register.simple_tag
def is_client_error(status_code):
    if status.is_client_error(status_code):
        return True
    else:
        return False


@register.simple_tag
def is_server_error(status_code):
    if status.is_server_error(status_code):
        return True
    else:
        return False


def reverse_status_code(status_code):
    """ Get status message by code """
    sentence = ""
    status_code = str(status_code)
    available_http_codes = [item for item in dir(status) if item.startswith("HTTP_")]
    for i in available_http_codes:
        if status_code in i:
            info = i.split(status_code+'_')
            words = info[1].split("_")
            sentence = (" ".join(words)).title()
    return sentence

@register.simple_tag
def status_info(request, status_code, user, status_code_detail):
    """
    Display status info if not success (HTTP_2xx)
    {% status_info request response.status_code user response.data.detail %}
    """
    status_code = int(status_code)
    optional_login_html = restapi_app.templatetags.internal_extras.optional_login(request)

    # If an overriding detail message hasn't been supplied, dig one out of the status code variables provided by DRF
    if not len(status_code_detail) > 0:
        status_code_detail = reverse_status_code(status_code)
    snippet = ""

    if status.is_informational(status_code):
        # 1XX
        pass
    if status.is_success(status_code):
        # 2XX
        if status_code == 204:
            # 204 NO CONTENT
            snippet = """
                <div class="col-md-12">
                    <div class="row-fluid text-center https-status-message">
                        <h1>There's nothing to see here.</h1>
                        <h2>{status_code_detail}</h2>
                        <h4>Status Code: {status_code}</h4>
                        <p>If you believe you are seeing this page in error, please <a href="" class="btn btn-default btn-xs">Contact Support </a>
                        </p>
                    </div>
                </div>
            """
            snippet = format_html(snippet, status_code=status_code,  status_code_detail=status_code_detail, optional_login=optional_login_html)

    if status.is_redirect(status_code):
        # 3XX
        pass
    if status.is_client_error(status_code):
        # 4XX
        snippet = """
                <div class="col-md-12" style="margin-top: 30px">
                    <div class="row-fluid text-center https-status-message">
                        <h1>Oops!</h1>
                        <h2>{status_code_detail}</h2>
                        <h4>Status Code: {status_code}</h4>
                        <p>If you believe you are seeing this page in error, please <a href="" class="btn btn-default btn-xs">Contact Support </a>
                        </p>
                    </div>
                    <div class="row-fluid text-center https-status-message">
        """
        if str(user) == 'AnonymousUser':
            snippet += "{optional_login}"
        snippet += "</div></div>"
        optional_login_html = restapi_app.templatetags.internal_extras.optional_login(request)
        snippet = format_html(snippet, status_code=status_code, request=request, user=user,
                              status_code_detail=status_code_detail, optional_login=optional_login_html)

    if status.is_server_error(status_code):
        # 5XX
        pass

    return mark_safe(snippet)

