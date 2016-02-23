"""asvo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.http import HttpResponseRedirect

urlpatterns = [
    # url(r'^asvo/', include('aatnode.urls', namespace='aatnode')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^asvo/', include('restapi_app.urls')),
    url(r'^$', lambda r: HttpResponseRedirect('asvo/')),
    #url(r'^/', include('aatnode.urls', namespace='aatnode')),
    # url(r'^ajax/custom-chained-view-url/$', AjaxChainedView.as_view(), name='ajax_chained_view'),
    #url(r'^ajax/chained-columns/$', AjaxChainedColumns.as_view(), name='ajax_chained_columns'),
    #url(r'^$', IndexView.as_view(), name='index'),
    #url(r'^query/$', queryForm.as_view(), name='queryForm'),
    # url(r'^$',homePage, name='homePage'),
    # url(r'^query/$', newForm),
]
