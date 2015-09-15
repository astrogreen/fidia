__author__ = 'lharischandra'
from django import forms
from astrospark import mediator

class QueryForm(forms.Form):
    query = forms.CharField(widget=forms.Textarea)

    def execute(self):
        # TODO: invoke execute_query in the astrospark with cleaned data
        q = self.cleaned_data.get('query')
        df = mediator.execute_query(q)


