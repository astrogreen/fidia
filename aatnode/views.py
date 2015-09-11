from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic
from .forms import QueryForm
from django.core.urlresolvers import reverse_lazy

# Create your views here.


class IndexView(generic.TemplateView):
    template_name = 'aatnode/index.html'

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


"""def index(request):
    return HttpResponse("Hello world. You're at the ASVO AAT NODE")"""


def querys(request):
    """
    This should take a bunch of request parameters and create a sparksql query out of them.
    :return:
    """
    # At this stage I have to assume the names of the form fields
    # This function might not required since there is a QueryView class above.


    pass
