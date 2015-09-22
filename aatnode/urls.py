__author__ = 'lharischandra'
from django.conf.urls import url

from . import views


#comment override
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    #url(r'^query/$', views.QueryView.as_view(), name='query'),
    url(r'^ajax/chained-columns/$', views.AjaxChainedColumns.as_view(), name='ajax_chained_columns'),
    url(r'^query/$', views.QueryForm.as_view(), name='queryForm'),
]