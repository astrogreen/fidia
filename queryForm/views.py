from django.shortcuts import render
from django.views import generic
from django.http import HttpResponseRedirect
from .forms import returnColumns
from clever_selects.views import ChainedSelectChoicesView
from .helpers import COLUMNS
from django.core.urlresolvers import reverse_lazy

# Create your views here.
# def homePage(request):
#     return render(request, 'homePage/home.html',)

class IndexView(generic.TemplateView):
    template_name = 'homePage/home.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['some_names'] = 'get values or objects'
        return context

class queryForm(generic.View):
    form_class = returnColumns
    template_name = 'form1/queryForm.html'
    initial = {'key': 'value'}

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # <process form cleaned data>
            print(request.POST)
            print(form.cleaned_data)
            return render(request, 'form1/queryForm.html', {
                'form': form,
                'message': (request.POST['cat'],request.POST.getlist('columns'),request.POST['tableType']),
                # 'error_message': "You didn't select a choice.",
            })
        else:
            return render(request, 'form1/queryForm.html', {
                'form': form,
                'message': '',
                'error_message': 'INVALID FORM',
            })

# def newForm(request):
#     if request.method == 'POST':
#         form = returnColumns(request.POST)
#         if form.is_valid():
#             print(request.POST)
#             print(form.cleaned_data)
#             return render(request, 'form1/queryForm.html', {
#                 'form': form,
#                 'message': (request.POST['cat'],request.POST.getlist('columns')),
#                 # 'error_message': "You didn't select a choice.",
#             })
#         else:
#             return render(request, 'form1/queryForm.html', {
#                 'form': form,
#                 'message': '',
#                 'error_message': 'INVALID FORM',
#             })
#     #if GET or other method create blank form
#     else:
#         form=returnColumns()
#     return render(request, 'form1/queryForm.html', {'form': form})


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