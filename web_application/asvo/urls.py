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
from django.conf import settings
from django.conf.urls.static import static

handler404 = "restapi_app.errorhandler.handler404"

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^asvo/', include('restapi_app.urls')),
    url(r'^asvo/', include('documentation.urls', namespace='documentation')),
    # url(r'^asvo/', include('download.urls')),
    url(r'^asvo/', include('data_browser.urls', namespace='data_browser')),
    # url(r'^asvo/', include('query.urls')),
    url(r'^asvo/', include('user.urls')),
    # url(r'^asvo/', include('schema.urls', namespace='schema')),
    url(r'^asvo/', include('schema_browser.urls', namespace='schema_browser')),
    url(r'^$', lambda r: HttpResponseRedirect('asvo/')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


