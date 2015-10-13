from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic
from .forms import QueryForm, ReturnQuery
from django.core.urlresolvers import reverse_lazy

from clever_selects.views import ChainedSelectChoicesView
from .helpers import COLUMNS

from astrospark import mediator

# pthon-sql library for building SQL queries in QueryForm.post() 
# (https://pypi.python.org/pypi/python-sql)
#import sql

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
    form_class = ReturnQuery
    template_name = 'aatnode/form1/queryForm.html'
    initial = {'key': 'value'}
    #success_url = reverse_lazy('aatnode:query')

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        select_fields=[]
        join_fields=[]
        filter_fields=[]
        type_fields=[]
        form_fields_as_list = list(form)
        for i in form_fields_as_list:
            if 'select_' in i.html_name:
                select_fields.append(i)
            if 'joinA_' in i.html_name:
                join_fields.append(i)
            if 'join_' in i.html_name:
                join_fields.append(i)
            if 'joinB_' in i.html_name:
                join_fields.append(i)
            if 'filter_' in i.html_name:
                filter_fields.append(i)
            if 'tableType' in i.html_name:
                type_fields.append(i)

        return render(request, self.template_name, {'form': form, 'selectFieldsCount':ReturnQuery.selectFieldsCount,'joinFieldsCount':ReturnQuery.joinFieldsCount, 'filterFieldsCount':ReturnQuery.filterFieldsCount, 'form_fields_as_list':form_fields_as_list, 'select_fields':select_fields, 'join_fields':join_fields,'filter_fields':filter_fields, 'type_fields':type_fields})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # <process form cleaned data>
            print(request.POST)
            print(form.cleaned_data)


            # Create the query here from POST data.
            #
            # Note: this code will rapidly become complex, and it should be
            # moved elsewhere. It is here for the moment becaue it is not
            # clear to me (AWG) where/how we should impliment this in the long
            # run. It fits here for the demonstrator. It could be incorporated
            # into FIDIA (and probably at least some of it will be), or it
            # could be part of a seperate module. A better understanding of
            # the astropy project "astroquery" is needed.

            # To simplify the creation of the query, which is nominally plain
            # SQL, this code adopts the python-sql module. Thust we can
            # programmatically generate our SQL with an existing library.

            # Get the list of tables:
            catalog_request = {}
            for key in request.POST.keys():
                if key.startswith("cat_"):
                    keyvalue = key[4:]
                    catalog_request[keyvalue] = ( 
                        key, 
                        request.POST.getlist('columns_' + keyvalue))


            # We need to create the query here from POST data. Is this the best way to do that?
            #query = 'Select ' + ', '.join(request.POST.getlist('columns_1')) + ' from ' + request.POST['cat_1']

            #qresults = mediator.execute_query(query)

            return render(request, 'aatnode/form1/queryForm.html', {
                'form': form,
                # 'message': request.POST.__str__ + "\n" + catalog_request.__str__,
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
