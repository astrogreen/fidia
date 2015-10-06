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


class ReturnQuery(ChainedChoicesForm):
    #create fields hidden on client side
    hiddenFields=10
    form_fields_as_list=[]
    for x in range(hiddenFields):
        exec("cat_" + str(x) + " = forms.ChoiceField(choices=[('', _(u'Select catalogue'))] + list(CAT), label='Table',required=False)")
        # exec("columns_" +str(x) + " = ChainedChoiceFieldMultiple(parent_field='cat_"+str(x) +"', ajax_url=reverse_lazy('aatnode:ajax_chained_columns'), empty_label=_(u'Select Columns'), label='Columns', required=False)")
        exec("columns_" +str(x) + " = ChainedChoiceFieldMultiple(parent_field='cat_"+str(x) +"', ajax_url=reverse_lazy('aatnode:ajax_chained_columns'), label='Columns', required=False)")
        form_fields_as_list.append('cat_'+str(x))

    tableType=forms.ChoiceField(choices=[('CSV','CSV'),('FITS','FITS'),('ASCII','ASCII')], label="Table Format")

    def __init__(self, *args, **kwargs):
        super(ReturnQuery, self).__init__(*args, **kwargs)

        for key in self.fields:
            self.fields[key].required = False

#TODO allow for return and filter fields (i.e, move cat_1 etc to returnCat)
