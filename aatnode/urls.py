__author__ = 'lharischandra'
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^home/$', views.IndexView.as_view(), name='index'),
    url(r'^documentation/$', views.DocView.as_view(), name='documentation'),
    url(r'^sign-in/$', views.SignIn.as_view(), name='sign-in'),
    url(r'^register/$', views.Register.as_view(), name='register'),
    url(r'^testground/$', views.TestingGroundView.as_view(), name='register'),

    url(r'^ajax/chained-columns/$', views.AjaxChainedColumns.as_view(), name='ajax_chained_columns'),
    url(r'^query-builder/$', views.QueryForm.as_view(), name='queryForm'),
    url(r'^csv_download/([\d\.]+)\.csv$', views.csv_downloader)
]