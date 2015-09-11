__author__ = 'lharischandra'
from django import forms

class QueryForm(forms.Form):
    query = forms.CharField(widget=forms.Textarea)

    def execute(self):
        # invoke execute_query in the astrospark with cleaned data
        q = self.cleaned_data.get('query')
        pass

