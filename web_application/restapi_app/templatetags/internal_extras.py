from __future__ import unicode_literals, absolute_import

import re
from django import template
from django.template import Library
from django.core.urlresolvers import reverse, NoReverseMatch, reverse_lazy, resolve
from django.core.exceptions import ObjectDoesNotExist
from django.http import QueryDict
from django.utils import six
from django.utils.encoding import iri_to_uri
from django.utils.html import escape, format_html
from django.utils.safestring import SafeData, mark_safe
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.text import normalize_newlines
from django.conf.urls import patterns, url, include
from django.contrib.staticfiles.templatetags.staticfiles import static
from rest_framework import status
from rest_framework.utils.urls import replace_query_param

register = template.Library()

# {% block status-info %}
#       {{ response.status_code }} {{ response.status_text }}
#     {% endblock status-info %}

@register.simple_tag
def status_is_success(status_code):
    if status.is_success(status_code):
        return True
    else:
        return False
    

@register.simple_tag
def status_info(request, status_code, user, status_code_detail):
    """
    Display status info if not success (HTTP_2xx)
    """
    if status.is_success(status_code):
        snippet = ""
    else:
        snippet = """
                <div class=" col-md-12" style="margin-top: 30px">
                    <div class="row-fluid text-center">
                        <h1>Oops!</h1>
                        <h2>{status_code_detail}</h2>
                        <h4>Status Code: {status_code}</h4>
                        <p>If you believe you are seeing this page in error, please <a href="" class="btn btn-default btn-xs">Contact Support </a>
                        </p>
                    </div>
                    <div class="text-center splitter">
                    <br>
                        {optional_login}
                    </div>
                </div>
            """
        snippet = format_html(snippet, status_code=status_code, request=request, user=user,
                              status_code_detail=status_code_detail, optional_login=optional_login(request))

    return mark_safe(snippet)


@register.simple_tag
def optional_logout(request, user):
    """
    Include a logout snippet if REST framework's logout view is in the URLconf.
    """
    try:
        logout_url = reverse('rest_framework:logout')
    except NoReverseMatch:
        snippet = format_html('<li class="navbar-text">{user}</li>', user=escape(user))
        return mark_safe(snippet)
    try:
        querylist_url = reverse('query-list')
    except NoReverseMatch:
        return ''
    try:
        logout_page = reverse('logout-page')
    except NoReverseMatch:
        return ''

    snippet = """<li class="dropdown">
        <a href="#" class="dropdown-toggle" data-toggle="dropdown">
            {user}
            <b class="caret"></b>
        </a>
        <ul class="dropdown-menu">
            <li><a href="{requests}">Query History</a></li>
            <li><a href='{href}?next={logout_page}'>Sign out <i class="fa fa-sign-out"></i></a></li>
        </ul>
    </li>"""
    snippet = format_html(snippet, user=escape(user), href=logout_url, requests=querylist_url, logout_page=logout_page)

    return mark_safe(snippet)


@register.simple_tag
def optional_login(request):
    """
    Include a login snippet if REST framework's login view is in the URLconf.
    """
    try:
        login_url = reverse('rest_framework:login')
    except NoReverseMatch:
        return ''
    try:
        register_url = reverse('user-register')
    except NoReverseMatch:
        return ''

    # On successful sign-in, prevent user being directed back to logout, register or login
    next_page = request.path
    next_url = escape(resolve(request.path_info).url_name)

    if request.user != 'AnonymousUser':
        if next_url == 'logout-page' or next_url == 'user-register' or next_url == 'login':
            next_page = ''

    # If this page is the registration form, drop register button
    if next_url == 'user-register':
        snippet = """<div class="user">
                    <a href='{login}?next={next}' class="signin">
                        <span>Sign In</span>
                        <i class="fa fa-lock"></i>
                    </a>
                </div>"""
    # If logged in, drop both buttons
    # elif request.user != 'AnonymousUser':
    #     snippet = ""
    # else:
    snippet = """<div class="user">
                <a href='{login}?next={next}' class="signin">
                    <span>Sign In</span>
                    <i class="fa fa-lock"></i>
                </a>
                <span>OR</span>
                <a href="{register}" class="register">
                    <span>Register</span>
                    <i class="fa fa-pencil-square-o"></i>
                </a>
            </div>"""
    snippet = format_html(snippet, login=login_url, register=register_url, next=next_page)
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


@register.filter
def ValueType(value):  # Only one argument.
    """returns the type of an object"""
    return type(value).__name__


@register.filter
def CapsSentence(value):  # Only one argument.
    """returns caps words"""
    words = value.split("_")
    sentence = (" ".join(words)).title()
    # .title capitalizes the first letter of every word in words list

    corrections = [['Rss', 'RSS'], ['Wcs', 'WCS'], ['Ra', 'RA'], ['Id', 'ID']]
    for arr_el in corrections:
        if arr_el[0] in sentence:
            sentence = sentence.replace(arr_el[0], arr_el[1])

    return sentence


@register.filter
def uppercase(value):  # Only one argument.
    """returns caps words"""
    return value.upper()


@register.filter
def lowercase(value):  # Only one argument.
    """returns caps words"""
    return value.lower()

@register.filter
def LineOnly(value):  # Only one argument.
    """returns formatted Line Values"""
    words = value.split("-")
    line = words[-1]
    temp = re.split('(\d+)', line)
    sentence = " ".join(temp)

    return sentence.upper()


@register.filter
def TraitTypeSplit(value):  # Only one argument.
    """returns formatted Line Values"""
    words = value.split("-")
    line = words[-1]
    # sentence = " ".join(words)
    # .title capitalizes the first letter of every word in words list
    return line.title()


@register.simple_tag
def add_query_param_trait(request, key, val, trait_name):
    """
    Add a query parameter to the current request url, and return the new url.
    edited: Append the trait property name to create a url of that endpoint
    """
    iri = request.get_full_path()
    uri = iri_to_uri(iri)+trait_name+'/'

    return escape(replace_query_param(uri, key, val))


@register.filter
def get_range(value):
    """
    Filter - returns a list containing range made from given value
    Usage (in template):

    <ul>{% for i in 3|get_range %}
      <li>{{ i }}. Do something</li>
    {% endfor %}</ul>

    Results with the HTML:
    <ul>
      <li>0. Do something</li>
      <li>1. Do something</li>
      <li>2. Do something</li>
    </ul>
    """
    return range(value)


@register.simple_tag
def get_pks(url, index):
    """
    split by /
    note that [-1] will give last item, [-2] the one before etc
    """
    pk_arr = url.split('/')
    return pk_arr[index]


@register.tag(name='captureas')
def do_captureas(parser, token):
    try:
        tag_name, args = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("'captureas' node requires a variable name.")
    nodelist = parser.parse(('endcaptureas',))
    parser.delete_first_token()
    return CaptureasNode(nodelist, args)


class CaptureasNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        output = self.nodelist.render(context)
        context[self.varname] = output
        return ''


@register.simple_tag
def surveylogoimglink(survey):
    """
    Snippet for survey logo/link combo
    """
    snippet = """
            <a href={surveylink} target="_blank">
                <img class="img-responsive pull-right {surveyclass}" src="{imgpath}">
            </a>
    """
    surveyclass=survey
    imgpath = static('restapi_app/img/logo/logo-'+survey+'.png')

    if survey == 'sami':
        surveylink="http://sami-survey.org/"
    elif survey == 'gama':
        surveylink="http://www.gama-survey.org/"
    else:
        surveylink=""

    snippet = format_html(snippet, surveylink=surveylink, surveyclass=surveyclass, imgpath=imgpath)
    return mark_safe(snippet)


@register.simple_tag
def fstrip_trailing_slash(url):
    """
    Snippet for stripping the trailing slash on a url
    Necessary for pages with anchor at the end

    """
    new_url = url.rstrip('/')
    return new_url
