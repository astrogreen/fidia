from django.conf.urls import url, include
import rest_framework.routers

import documentation.views
import restapi_app.views

router = rest_framework.routers.SimpleRouter()

router.register(r'docs/topics', documentation.views.TopicViewset, base_name="topic")
router.register(r'docs/articles', documentation.views.ArticleViewset, base_name="article")

urlpatterns = [
    url(r'', include(router.urls)),

    url(r'docs/faq/$', restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='documentation/faq.html'), name='faq'),
    url(r'docs/syntax/$', restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='documentation/syntax.html'), name='syntax'),
]