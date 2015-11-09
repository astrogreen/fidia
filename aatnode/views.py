import os
import time

# Set up logging
import logging
log = logging.getLogger(__name__)


# Django Imports
from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.views.static import serve

from clever_selects.views import ChainedSelectChoicesView

# Relative Package Imports
from .forms import QueryForm, ReturnQuery
from .helpers import COLUMNS


# SQLAlchemy for building queries in QueryForm.post()
# (http://docs.sqlalchemy.org/en/rel_1_0/core/tutorial.html)
#import sqlalchemy as sql

from fidia.fidia.archive.asvo_spark import AsvoSparkArchive

import json


def csv_downloader(request, query_id):
    """Simple View to return a cached CSV file."""

    # @TODO: Check that the query_id actually refers to a cached result.

    # Use Django file serving to send the file
    # (see https://docs.djangoproject.com/en/1.8/howto/static-files/)
    log.info("Sending cached CSV files for query id '%s'", query_id)
    filepath = csv_cache_filename(query_id)
    if not os.path.exists(filepath):
        log.warning("Cached CSV File '%s' not found", filepath)
    return serve(request, filepath, document_root='/')


class IndexView(generic.TemplateView):
    template_name = 'aatnode/home/home.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['some_names'] = 'get values or objects'
        return context

class TestingGroundView(generic.TemplateView):
    template_name = 'aatnode/testpage/testpage.html'

    def get_context_data(self, **kwargs):
        context = super(TestingGroundView, self).get_context_data(**kwargs)
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
    template_name = 'aatnode/form/queryForm.html'
    initial = {'key': 'value'}
    #success_url = reverse_lazy('aatnode:query')

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        select_fields = []
        join_fields = []
        filter_fields = []
        type_fields = []
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

        return render(request, self.template_name,
                      {'form': form,
                       'selectFieldsCount': ReturnQuery.selectFieldsCount,
                       'joinFieldsCount': ReturnQuery.joinFieldsCount,
                       'filterFieldsCount': ReturnQuery.filterFieldsCount,
                       'form_fields_as_list': form_fields_as_list,
                       'select_fields': select_fields,
                       'join_fields': join_fields,
                       'filter_fields': filter_fields,
                       'type_fields': type_fields})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            # <process form cleaned data>
            print(request.POST)
            print(form.cleaned_data)

            # Define a query ID for this query:
            query_id = "{0:.2f}".format(time.time())
            log.info("Query ID '%s' processing", query_id)
            # TODO: Save this in the UI for use when requesting the CSV file.

            # Create the SQL Query from the post data.
            query = build_query(request.POST)
            log.info("Query ID '%s' query_string: <<%s>>", query_id, query)

            # Get FIDIA Sample Object
            sample = AsvoSparkArchive().new_sample_from_query(query)

            # Produce JSON representation of result table
            json_table = sample.tabular_data().to_json()

            # Produce cached CSV results for potential download and save them to temporary directory
            csv_filename = csv_cache_filename(query_id)
            sample.tabular_data().to_csv(csv_filename)
            log.info("Query ID '%s' CSV written to '%s'", query_id, csv_filename)

            # Download URL to pass to web template
            csv_url = "/csv_download/" + query_id + ".csv"

            return render(request, 'aatnode/form/queryResults.html', {
                'sql_query': query,
                'json_data':json_table,
                # 'json_data': json.dumps(json_table),
                'csv_download_url': csv_url,
            })

        else:
            return render(request, 'aatnode/form/queryForm.html', {
                'form': form,
                'query_data': '',
                'sql_query': 'INVALID FORM',
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



# def index(request):
#     return HttpResponse("Hello world. You're at the ASVO AAT NODE")


class QueryResultsView(generic.TemplateView):
    template_name = 'aatnode/queryresults.html'

    # TODO: This is a redirect page. Soooo how to feed the data to this?


def csv_cache_filename(query_id):
    """Generate a absolute path+filename for a CSV cache file.

    Creates the CACHE_DIR directory if required.

    """

    if not os.path.exists(settings.CACHE_DIR):
        os.mkdir(settings.CACHE_DIR)
    return settings.CACHE_DIR + query_id + ".csv"


def build_query(request):
    """
    Create the query here from POST data.

    :param request: A QueryDict which is the request.POST data from the form.

    Note: this code will rapidly become complex, and it may need to be
    moved elsewhere. It is here for the moment becaue it is not
    clear to me (AWG) where/how we should impliment this in the long
    run. It fits here for the demonstrator. It could be incorporated
    into FIDIA (and probably at least some of it will be), or it
    could be part of a seperate module. A better understanding of
    the astropy project "astroquery" is needed.

    :return: Query string suitable for handing to Spark.

    """

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
    for table, columns in elements_of(request, "select_cat_", "select_columns_"):
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
            elements_of(request, "joinA_cat_", "joinA_columns_", "join_type_", "joinB_cat_", "joinB_columns_"):
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
        query += request["select_cat_0"]

    # Check if there are any filter values, if so generate the WHERE part of the query
    if request["filter_value_0"] != '':
        query += " WHERE "
        for table, col, op, value in \
                elements_of(request, "filter_cat_", "filter_columns_", "filter_operators_", "filter_value_"):
            if table != '':
                query += table + "." + col + " "
                if op == 'BETWEEN':
                    query += operator_map[op] + " " + " AND ".join(value.split(",")) + " AND "
                else:
                    query += operator_map[op] + " " + value + " AND "
        # Remove final AND:
        query = query[:-5]

    # We need to create the query here from POST data. Is this the best way to do that?
    #query = 'Select ' + ', '.join(request.getlist('columns_1')) + ' from ' + request['cat_1']

    return query
