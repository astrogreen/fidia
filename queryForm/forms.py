from django import forms
# from .models import allData, DMU
from clever_selects.form_fields import ChainedChoiceField
from clever_selects.forms import ChainedChoicesForm, ChainedChoicesModelForm
from django.core.urlresolvers import reverse_lazy
from clever_selects.form_fields import ChainedChoiceField, ChainedChoiceFieldMultiple

from django.utils.translation import ugettext_lazy as _
from .helpers import CAT

class returnColumns(ChainedChoicesForm):
    cat = forms.ChoiceField(choices=[('', _(u'Select a cat'))] + list(CAT), label='Table')
    #columns = ChainedChoiceField(parent_field='cat', ajax_url=reverse_lazy('ajax_chained_columns'), empty_label=_(u'Select column'))
    # columns = ChainedChoiceField(parent_field='cat', ajax_url='/ajax/chained-columns/', empty_label=_(u'Select column'))
    columns = ChainedChoiceFieldMultiple(parent_field='cat', ajax_url='/ajax/chained-columns/', empty_label=_(u'Select column'), label='Columns')
    tableType=forms.ChoiceField(choices=[('CSV','CSV'),('FITS','FITS'),('ASCII','ASCII')], label="Table Format")