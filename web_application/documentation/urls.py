from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import rest_framework.routers


import documentation.views


router = rest_framework.routers.SimpleRouter()

router.register(r'docs/topics', documentation.views.TopicViewset, base_name="topic")
router.register(r'docs/articles', documentation.views.ArticleViewset, base_name="article")
# router.register(r'docs/topics/(?P<topic_slug>[^/]+)/articles', documentation.views.ArticleViewset, base_name="articles")


# router.register(r'doc/(?i)sami', documentation.views.SAMIDocumentation, base_name="sami-docs")
# router.register(r'doc/data-browser', documentation.views.DataBrowserDocumentation, base_name="data-browser-docs")


urlpatterns = [
    url(r'doc/$', documentation.views.DocumentationRoot.as_view(), name='root'),
    url(r'', include(router.urls)),



]




import rest_framework.routers


# Nested routes for sample (SAMI)
