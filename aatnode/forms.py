__author__ = 'lharischandra'
from django import forms
from astrospark import mediator
from clever_selects.forms import ChainedChoicesForm
from clever_selects.form_fields import ChainedChoiceFieldMultiple

from django.utils.translation import ugettext_lazy as _
from .helpers import CAT

from django.core.urlresolvers import reverse_lazy

class QueryForm(forms.Form):
    query = forms.CharField(widget=forms.Textarea)

    def execute(self):
        # TODO: invoke execute_query in the astrospark with cleaned data
        q = self.cleaned_data.get('query')
        df = mediator.execute_query(q)


class ReturnColumns(ChainedChoicesForm):
    cat = forms.ChoiceField(choices=[('', _(u'Select a cat'))] + list(CAT), label='Table')
    #columns = ChainedChoiceField(parent_field='cat', ajax_url=reverse_lazy('ajax_chained_columns'), empty_label=_(u'Select column'))
    # columns = ChainedChoiceField(parent_field='cat', ajax_url='/ajax/chained-columns/', empty_label=_(u'Select column'))
    columns = ChainedChoiceFieldMultiple(parent_field='cat', ajax_url=reverse_lazy('aatnode:ajax_chained_columns'), empty_label=_(u'Select column'), label='Columns')
    tableType=forms.ChoiceField(choices=[('CSV','CSV'),('FITS','FITS'),('ASCII','ASCII')], label="Table Format")
    testSurvey=forms.ChoiceField(choices=[('Select Survey','Select Survey')], label='Survey')
    testCat=forms.ChoiceField(choices=[('test-CAT','test-CAT')], label='Catalogue')
    testColumns=forms.ChoiceField(choices=[('test-CAT-COLS','test-CAT-COLS')], label='Columns')