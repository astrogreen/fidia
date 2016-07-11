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

@register.filter
def QualifierOnly(value):  # Only one argument.
    """returns formatted Line Values"""
    words = value.split("-")
    line = words[-1]
    temp = re.split('(\d+)', line)
    sentence = " ".join(temp)

    if words[0] == "Line Map":
        sentence = sentence.upper()
        if 'HALPHA' in sentence:
            sentence = 'Hα'
        if 'HBETA' in sentence:
            sentence = 'Hβ'

    return sentence