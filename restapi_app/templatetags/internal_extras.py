from __future__ import unicode_literals, absolute_import
from django import template
from django.core.urlresolvers import reverse, NoReverseMatch, reverse_lazy
from django.http import QueryDict
from django.utils import six
from django.utils.encoding import iri_to_uri
from django.utils.html import escape, format_html
from django.utils.safestring import SafeData, mark_safe
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.text import normalize_newlines


register = template.Library()

@register.simple_tag
def web_logout(request, user):
    """
    Include a logout snippet if REST framework's logout view is in the URLconf.
    """
    try:
        logout_url = reverse('rest_framework:logout')
        # requests_url = reverse('snippet-list')
    except NoReverseMatch:
        return '<li class="navbar-text">{user}</li>'.format(user=user)

    snippet = """<li class="dropdown">
        <a href="#" class="dropdown-toggle" data-toggle="dropdown">
            {user}
            <b class="caret"></b>
        </a>
        <ul class="dropdown-menu">
            <li><a href="">Requests</a></li>
            <li><a href='{href}?next={next}'>Log out</a></li>
        </ul>
    </li>"""

    return snippet.format(user=user, href=logout_url, next=escape(request.path))

@register.simple_tag
def web_login(request):
    """
    Include a login snippet if REST framework's login view is in the URLconf.
    """
    try:
        login_url = reverse('rest_framework:login')
    except NoReverseMatch:
        return ''

    snippet="""<div class="user">
                    <a href='{href}?next={next}' class="signin">
                        <span>Sign In</span>
                        <i class="fa fa-lock"></i>
                    </a>
                    <span>OR</span>
                    <a href="" class="register">
                        <span>Register</span>
                        <i class="fa fa-pencil-square-o"></i>
                    </a>
                </div>"""
    snippet = format_html(snippet, href=login_url, next=escape(request.path))

    return mark_safe(snippet)


def remove_newlines(text):
    """
    Removes all newline characters from a block of text.
    """
    # First normalize the newlines using Django's nifty utility
    normalized_text = normalize_newlines(text)
    # Then simply remove the newlines like so.
    return mark_safe(normalized_text.replace('\n', ' '))
remove_newlines.is_safe = True
remove_newlines = stringfilter(remove_newlines)
register.filter(remove_newlines)