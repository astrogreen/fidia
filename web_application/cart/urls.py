from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
import rest_framework.routers

import restapi_app.views
import cart.views

router = rest_framework.routers.SimpleRouter()

# router.register(r'download', cart.views.CartViewSet, base_name='cart')


urlpatterns = [
    url(r'', include(router.urls)),
    url(r'download/', cart.views.CartView.as_view(), name='cart-list'),
    # url(r'cart/$',
    #     restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='cart/cart.html'),
    #     name='cart'),
    url(r'cart/dummy-item/$',
        restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='cart/dummy_item.html'),
        name='dummy-item'),
    url(r'dummy-cart/$',
        restapi_app.views.TemplateViewWithStatusCode.as_view(template_name='cart/dummy_item.html'),
        name='dummy-cart'),
]


# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) allows
# Django to serve these files (without explicitly writing them out per view)
