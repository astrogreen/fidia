from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic
from .forms import QueryForm, ReturnQuery
from django.core.urlresolvers import reverse_lazy

from clever_selects.views import ChainedSelectChoicesView
from .helpers import COLUMNS


# SQLAlchemy for building queries in QueryForm.post()
# (http://docs.sqlalchemy.org/en/rel_1_0/core/tutorial.html)
#import sqlalchemy as sql

from fidia.fidia.archive.asvo_spark import AsvoSparkArchive

# Create your views here.


class IndexView(generic.TemplateView):
    template_name = 'aatnode/homePage/home.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['some_names'] = 'get values or objects'
        return context


class DocView(generic.TemplateView):
    template_name = 'aatnode/documentation/documentation.html'

    def get_context_data(self, **kwargs):
        context = super(DocView, self).get_context_data(**kwargs)
        context['some_names'] = 'get values or objects'
        return context

class SignIn(generic.TemplateView):
    template_name = 'aatnode/user/sign-in.html'

    def get_context_data(self, **kwargs):
        context = super(SignIn, self).get_context_data(**kwargs)
        context['some_names'] = 'get values or objects'
        return context

class Register(generic.TemplateView):
    template_name = 'aatnode/user/register.html'

    def get_context_data(self, **kwargs):
        context = super(Register, self).get_context_data(**kwargs)
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

        return render(request, self.template_name, {'form': form, 'selectFieldsCount':ReturnQuery.selectFieldsCount,
                                                    'joinFieldsCount':ReturnQuery.joinFieldsCount,
                                                    'filterFieldsCount':ReturnQuery.filterFieldsCount,
                                                    'form_fields_as_list':form_fields_as_list,
                                                    'select_fields':select_fields, 'join_fields':join_fields,
                                                    'filter_fields':filter_fields, 'type_fields':type_fields})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
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


            # The contents of the POST object are described here:
            # https://docs.djangoproject.com/en/1.8/ref/request-response/#django.http.QueryDict

            def elements_of(request, *args):
                """Iterator which iterates over elements of the request dictionary with the same base name.

                request: the QueryDict to iterate over.
                args: the list of key base strings to iterate over

                Description:

                    Given a request dictionary like the following:

                    {tab1, tab2, tab3, tab4,
                    col1, col2, col3, col4, etc. Each key is a string followed by a numeric index. (Additional keys
                    may be present, without affecting this function). This iterator is given the base strings as arguments

                """

                index = 0
                while (args[0] + str(index)) in request:
                    key_list = [key + str(index) for key in args]

                    value_list = []
                    for key in key_list:
                        value = request.getlist(key)
                        if isinstance(value, list) and len(value) == 1:
                            value = value[0]
                        value_list.append(value)

                    yield tuple(value_list)
                    index += 1

            operator_map = {
                'EQUALS': " = ",
                'LESS_THAN': " < ",
                'LESS_THAN_EQUALS': " <= ",
                'GREATER_THAN': " > ",
                'GREATER_THAN_EQUALS': " >= ",
                'BETWEEN': " BETWEEN ",
                'LIKE': " LIKE ",
                'NULL': " NULL "
            }
            join_map = {
                'INNER_JOIN': " INNER ",
                'OUTER_JOIN': " OUTER ",
                'LEFT_JOIN': " LEFT ",
                'RIGHT_JOIN': " RIGHT ",
                'FULL_JOIN': " FULL ",

            }

            # String containing the HiveSQL query
            query = ""

            # Generate the SELECT part of the query:
            query += "SELECT "
            for table, columns in elements_of(request.POST, "select_cat_", "select_columns_"):
                if table != '':
                    # Otherwise skip blank tables in the request.
                    for col in columns:
                        query += table + "." + col + ", "
            # Remove the final ", " before continuing
            query = query[:-2]

            # Generate the FROM and JOIN part of the query
            query += " FROM "
            first = True
            for left, left_col, join_type, right, right_col in \
                    elements_of(request.POST, "joinA_cat_", "joinA_columns_", "join_type_", "joinB_cat_", "joinB_columns_"):
                if left != '':
                    if first:
                        # First join statement must include lefthand table name
                        query += left
                        first = False
                    query += join_map[join_type] + " JOIN " + right
                    query += " ON " + left + "." + left_col
                    query += " = "
                    query += right + "." + right_col + " "
            if first:
                # There were no join statements provided, so use the table from the select:
                query += request.POST["select_cat_0"]

            # Check if there are any filter values, if so generate the WHERE part of the query
            if(request.POST["filter_value_0"] != ''):
                query += " WHERE "
                for table, col, op, value in \
                        elements_of(request.POST, "filter_cat_", "filter_columns_", "filter_operators_", "filter_value_"):
                    if table != '':
                        query += table + "." + col + " "
                        if op == 'BETWEEN':
                            query += operator_map[op] + " " + " AND ".join(value.split(",")) + " AND "
                        else:
                            query += operator_map[op] + " " + value + " AND "
                # Remove final AND:
                query = query[:-5]

            # We need to create the query here from POST data. Is this the best way to do that?
            #query = 'Select ' + ', '.join(request.POST.getlist('columns_1')) + ' from ' + request.POST['cat_1']

            sample = AsvoSparkArchive().new_sample_from_query(query)

            return render(request, 'aatnode/form1/queryForm.html', {
                'form': form, 'selectFieldsCount':ReturnQuery.selectFieldsCount,
                'joinFieldsCount':ReturnQuery.joinFieldsCount, 'filterFieldsCount':ReturnQuery.filterFieldsCount,
                'form_fields_as_list':form_fields_as_list, 'select_fields':select_fields, 'join_fields':join_fields,
                'filter_fields':filter_fields, 'type_fields':type_fields,
                'message': sample.tabular_data().to_html(classes='table table-hover',bold_rows=False),
                'error_message': query,
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
