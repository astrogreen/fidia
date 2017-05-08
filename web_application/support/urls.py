from django.conf.urls import url, include
import rest_framework.routers
import support.views

router = rest_framework.routers.SimpleRouter()

router.register(r'contact', support.views.Contact, base_name='contact')
router.register(r'bug-report', support.views.BugReport, base_name='bug-report')


urlpatterns = [
    url(r'', include(router.urls)),
]
