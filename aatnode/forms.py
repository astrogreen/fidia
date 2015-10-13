__author__ = 'lharischandra'
import json
from django import forms
from astrospark import mediator
from clever_selects.forms import ChainedChoicesForm
from clever_selects.form_fields import ChainedChoiceFieldMultiple, ChainedChoiceField

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
    selectFieldsCount=5
    joinFieldsCount=selectFieldsCount-1
    filterFieldsCount=selectFieldsCount
    #these loops must be separate in order for the view to pick out the correct fields
    for x in range(selectFieldsCount):
        if x == 0:
            exec("select_cat_" + str(x) + " = forms.ChoiceField(choices=[('', _(u'Catalogue'))] + list(CAT),required=True)")
            exec("select_columns_" +str(x) + " = ChainedChoiceFieldMultiple(parent_field='select_cat_"+str(x) +"', ajax_url=reverse_lazy('aatnode:ajax_chained_columns'), label='Columns', required=True)")
        else:
            exec("select_cat_" + str(x) + " = forms.ChoiceField(choices=[('', _(u'Catalogue'))] + list(CAT),required=False)")
            exec("select_columns_" +str(x) + " = ChainedChoiceFieldMultiple(parent_field='select_cat_"+str(x) +"', ajax_url=reverse_lazy('aatnode:ajax_chained_columns'), label='Columns', required=False)")

    for x in range(joinFieldsCount):
        exec("joinA_cat_" + str(x) + " = forms.ChoiceField(choices=[('', _(u'Catalogue'))] + list(CAT),required=False)")
        exec("joinA_columns_" +str(x) + " = ChainedChoiceField(parent_field='joinA_cat_"+str(x) +"', ajax_url=reverse_lazy('aatnode:ajax_chained_columns'), label='Columns', required=False)")
        exec("join_type_" + str(x)+ " = forms.ChoiceField(choices=[('INNER_JOIN','Inner'),('OUTER_JOIN','Outer'),('LEFT_JOIN','Left'),('RIGHT_JOIN','Right'),('FULL_JOIN','Full')],required=False)")
        exec("joinB_cat_" + str(x) + " = forms.ChoiceField(choices=[('', _(u'Catalogue'))] + list(CAT),required=False)")
        exec("joinB_columns_" +str(x) + " = ChainedChoiceField(parent_field='joinB_cat_"+str(x) +"', ajax_url=reverse_lazy('aatnode:ajax_chained_columns'), label='Columns', required=False)")

    for x in range(filterFieldsCount):
        exec("filter_cat_" + str(x) + " = forms.ChoiceField(choices=[('', _(u'Catalogue'))] + list(CAT),required=False)")
        exec("filter_columns_" +str(x) + " = ChainedChoiceField(parent_field='filter_cat_"+str(x) +"', ajax_url=reverse_lazy('aatnode:ajax_chained_columns'), label='Columns', required=False)")
        exec("filter_checkbox_" +str(x) + " = forms.BooleanField(label='Not',required=False)")
        exec("filter_operators_" + str(x)+ " = forms.ChoiceField(choices=[('EQUALS','='),('LESS_THAN','<'),('LESS_THAN_EQUALS','<='),('GREATER_THAN','>'),('GREATER_THAN_EQUALS','>='),('BETWEEN','BETWEEN'),('LIKE','LIKE'),('NULL','NULL')],required=False)")
        exec("filter_value_" +str(x) + " = forms.CharField(required=False)")

    tableType=forms.ChoiceField(choices=[('CSV','CSV'),('FITS','FITS'),('ASCII','ASCII')], label="Table Format")

    def __init__(self, *args, **kwargs):
        super(ReturnQuery, self).__init__(*args, **kwargs)

        for key in self.fields:
            self.fields[key].required = False

#TODO allow for return and filter fields (i.e, move cat_1 etc to returnCat)
