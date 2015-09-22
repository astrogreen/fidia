__author__ = 'lharischandra'
import json
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
    def __init__(self, *args, **kwargs):
        super(ReturnColumns, self).__init__(*args, **kwargs)

        for key in self.fields:
            self.fields[key].required = False
    # cat = forms.ChoiceField(choices=[('', _(u'Select a cat'))] + list(CAT), label='Table')
    # columns = ChainedChoiceFieldMultiple(parent_field='cat', ajax_url=reverse_lazy('aatnode:ajax_chained_columns'), empty_label=_(u'Select column'), label='Columns')
    #create fields hidden on client side
    for x in range(1,11):
        exec("cat_" + str(x) + " = forms.ChoiceField(choices=[('', _(u'Select a cat'))] + list(CAT), label='Table',required=False)")
        exec("columns_" +str(x) + " = ChainedChoiceFieldMultiple(parent_field='cat_"+str(x) +"', ajax_url=reverse_lazy('aatnode:ajax_chained_columns'), empty_label=_(u'Select column'), label='Columns', required=False)")

    # tableType=forms.ChoiceField(choices=[('CSV','CSV'),('FITS','FITS'),('ASCII','ASCII')], label="Table Format")
    # testSurvey=forms.ChoiceField(choices=[('Survey','Survey')], label='Survey')
    # testCat=forms.ChoiceField(choices=[('test-CAT','test-CAT')], label='Catalogue')
    # testColumns=forms.MultipleChoiceField(choices=[('test-CAT-COLS','test-CAT-COLS')], label='Columns')