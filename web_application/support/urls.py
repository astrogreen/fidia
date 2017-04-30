from django.conf.urls import url, include
import rest_framework.routers
import support.views

router = rest_framework.routers.SimpleRouter()

router.register(r'contact', support.views.Contact, base_name='contact')


urlpatterns = [
    url(r'', include(router.urls)),
]


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
