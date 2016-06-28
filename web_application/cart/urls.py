from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
import rest_framework.routers

import cart.views

router = rest_framework.routers.SimpleRouter()

# router.register(r'download', cart.views.CartViewSet, base_name='cart')


urlpatterns = [
    url(r'', include(router.urls)),
    url(r'download/', cart.views.CartView.as_view(), name='cart-list')
]


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
