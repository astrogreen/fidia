from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic
from .forms import QueryForm, ReturnColumns
from django.core.urlresolvers import reverse_lazy

from clever_selects.views import ChainedSelectChoicesView
from .helpers import COLUMNS


from fidia.archive.asvo_spark import AsvoSparkArchive

# Create your views here.


class IndexView(generic.TemplateView):
    template_name = 'aatnode/homePage/home.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['some_names'] = 'get values or objects'
        return context


class QueryView(generic.FormView):
    template_name = 'aatnode/queryform.html'
    form_class = QueryForm
    success_url = reverse_lazy('aatnode:index')

    def form_valid(self, form):
        form.execute()
        return super(QueryView, self).form_valid(form)


class QueryForm(generic.View):
    form_class = ReturnColumns
    template_name = 'aatnode/form1/queryForm.html'
    initial = {'key': 'value'}
    #success_url = reverse_lazy('aatnode:query')

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # <process form cleaned data>
            print(request.POST)
            print(form.cleaned_data)
            # We need to create the query here from POST data. Is this the best way to do that?
            query = 'Select ' + ', '.join(request.POST.getlist('columns_1')) + ' from ' + request.POST['cat_1']

            sample = AsvoSparkArchive().new_sample_from_query(query)

            return render(request, 'aatnode/form1/queryForm.html', {
                'form': form,
                'message': sample.tabular_data().to_csv(),
                # 'error_message': "You didn't select a choice.",
            })
        else:
            return render(request, 'aatnode/form1/queryForm.html', {
                'form': form,
                'message': '',
                'error_message': 'INVALID FORM',
            })



class AjaxChainedColumns(ChainedSelectChoicesView):
    def get_choices(self):
        choices = []
        try:
            cat_columns = COLUMNS[self.parent_value]
            for columns in cat_columns:
                choices.append((columns, columns))
        except KeyError:
            return []
        return choices





"""def index(request):
    return HttpResponse("Hello world. You're at the ASVO AAT NODE")"""

class QueryResultsView(generic.TemplateView):
    template_name = 'aatnode/queryresults.html'

    # TODO: This is a redirect page. Soooo how to feed the data to this?


def querys(request):
    """
    This should take a bunch of request parameters and create a sparksql query out of them.
    :return:
    """
    # At this stage I have to assume the names of the form fields
    # This function might not required since there is a QueryView class above.


    pass
