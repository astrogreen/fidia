import random, collections, json
from django.contrib.auth.models import User
from django.http.response import HttpResponseRedirect
from django.contrib.auth import authenticate, login

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions, throttling
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

import restapi_app.exceptions
import restapi_app.renderers
import restapi_app.permissions

import download.serializers
import download.models


# Implement a list/retrieve?
# saves previous downloaded list (json only). post to view implements the download.
# get - single retrieve or list of previous downloads. Yup good stuff. data is json and reconstructed in the view.
# create == cart
# download history


class DownloadCreateView(generics.CreateAPIView):
    """
    Download Viewset. Create new download request, view download history, re-issue a download on a particular retrieve.
    """
    serializer_class = download.serializers.DownloadCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    breadcrumb_list = []

    def get_queryset(self):
        """
        Download queryset filtered by current user
        """
        user = self.request.user
        return download.models.Download.objects.filter(owner=user).order_by('-updated')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get(self, request, format=None):
        """
        Return the blank form for a POST request
        """
        DownloadCreateView.breadcrumb_list.extend(['Download'])
        return Response()


class DownloadListView(generics.ListAPIView):
    """
    Download History List
    """
    serializer_class = download.serializers.DownloadSerializer
    permission_classes = [permissions.IsAuthenticated]
    breadcrumb_list = ['Download History']

    class DownloadListRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'download/download-list.html'

    renderer_classes = (DownloadListRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def get_queryset(self):
        """
        Download queryset filtered by current user
        """
        user = self.request.user
        return download.models.Download.objects.filter(owner=user).order_by('-updated')


class DownloadRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    """
    Retrieve or destroy a particular Download object
    """
    serializer_class = download.serializers.DownloadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Download queryset filtered by current user
        """
        user = self.request.user
        return download.models.Download.objects.filter(owner=user).order_by('-updated')

# class DownloadItem(object):
#     def __init__(self, id=None, url_list=None, **kwargs):
#         self.id = id
#         self.url_list = self.get_url_list(url_list)
#         self.ao = self.get_ao(url_list)
#         # for field in ('id', 'url', 'ao', 'format'):
#         #     setattr(self, field, kwargs.get(field, None))
#
#     def get_ao(self, url_list):
#         j = url_list[0]
#         return j.split('/asvo/sami/')[1].split('/')[0]
#
#     def get_url_list(self, url_list):
#         url_dict = {}
#         for url in url_list:
#             url_dict[url] = self.get_format(url)
#         return url_dict
#         # return json.loads('{"urllist": {"url": "format"}}')
#
#     def get_format(self, url):
#         """ Priority: format taken from url string then attempt to sniff best format to return """
#         if len(url.split('?format=')) > 1:
#             return url.split('?format=')[1]
#         else:
#             # TODO have to do some sniffing here to find available formats and send most appropriate
#             return 'fits'
#
#
# download_dict = {
#     1: DownloadItem(id=1, url_list=['/asvo/sami/1234/trait/traitprop?format=json', '/asvo/sami/1234/trait/?format=csv']),
#     # 2: CartItem(id=2, url='/asvo/sami/4678/trait?format=csv', ao='xordoquy', format='test'),
#     # 3: CartItem(id=3, url='/asvo/sami/1234/trait/subtrait/traitproperty', ao='xordoquy', format='test'),
#     # 4: CartItem(id=4, url='/asvo/sami/645123/trait/subtrait/traitproperty', ao='xordoquy', format='test'),
# }


# class DownloadView(generics.ListCreateAPIView):
#     """
#     Shopping cart is available to the api - browsable and json.
#     """
#     serializer_class = cart.serializers.CartSerializer
#     queryset = cart_dict
#
#     def get(self, request, *args, **kwargs):
#         serializer = cart.serializers.CartSerializer(
#             instance=cart_dict.values(), many=True)
#         return Response(serializer.data)
#
#     def post(self, request, *args, **kwargs):
#         """ Handle data download from cart dict: take json list, return  """
#         return 'data'
#
# #
# class CartView(views.APIView):
#     """
#     Download data from shopping cart. Uses session storage to persist list.
#     """
#     # renderer_classes = [renderers.BrowsableAPIRenderer, renderers.JSONRenderer]
#     # template_name = 'cart/shopping-cart.html'
#     # # serializer_class = cart.serializers.CartSerializer
#     #
#     # def get_queryset(self):
#     #     return self.request.session['cart']
#     #
#     # def get(self, request, format=None):
#     #     """
#     #     Return a list of all users.
#     #     """
#     #     request.session['cart'] = CartItem(ao='654', url='/asvo/sami/test/this/url', d_format='test')
#     #     cart = request.session.get('cart', {})
#     #
#     #     return Response(cart)
#
# # # Method for getting items in dict
#     # def view_cart(self, request):
#     #     cart = request.session.get('cart', {})
#     #
#     # def add_to_cart(self, request, url, quantity):
#     #     cart = request.session.get('cart', {})
#     #     request.session['cart'] = cart
#
#
#
#
#
# class CartItem(object):
#     """
#     Cart items are dict with key astro_obj_name and address of piece of data you want to download
#     """
#     def __init__(self, url=None, ao=None, d_format=None, *args, **kwargs):
#         self.ao = ao
#         self.url = url
#         self.d_format = d_format
#
#
#     # def __repr__(self):
#     #     return u'CartItem Address (%s)' % self.url
#     #
#     # def __ao__(self, url):
#     #     """ Split url and get AO """
#     #     ao = url.split('asvo/sami/')[0].split('/')[0]
#     #     return str(ao)
#     #
#     # def __dformat__(self, url):
#     #     return 'fits'
#
#
# # class Cart(object):
# #     """
# #     A cart that lives in the session.
# #     """
# #     def __init__(self, session, session_key=None):
# #         self._items_dict = {}
# #         self.session = session
# #         self.session_key = session_key
# #
# #         # if self.session_key in self.session:
# #         #     # Rebuild the cart from previously serialized representation
# #         #
# #         #     cart_represenation = self.session[self.session_key]
# #         #     ...
# #
# #     def __contains__(self, url):
# #         """ Checks if the url is in the cart
# #         """
# #         return url in self.urls
# #
# #     def get_queryset(self):
# #         pass
# #
# #     def update_session(self):
# #         """
# #         Serializes the cart data, saves it to session and marks session as modified.
# #         """
# #         self.session[self.session_key] = self.cart_serializable
# #         self.session.modified = True
# #
# #     def add(self, url):
# #         """ Adds or creates urls in cart. For existing urls, nothing happens.
# #         """
# #         # get ao and d_format
# #         ao = CartItem(url).ao
# #         self._items_dict[ao] = CartItem(url)
# #         self.update_session()
# #
# #     def remove(self, url):
# #         if url in self.urls:
# #             ao = CartItem(url).ao
# #             del self._items_dict[ao][url]
# #             self.update_session()
# #
# #     def clear(self):
# #         """ Remove all items """
# #         self._items_dict = {}
# #         self.update_session()
# #
# #     @property
# #     def items(self):
# #         """ List of cart data pieces """
# #         return self._items_dict.values()
# #
# #     @property
# #     def cart_serializable(self):
# #         """ The serializable representation of the cart.
# #             {
# #                 'sami_6546': {
# #                         'data_piece_url1': 'format1,
# #                         'data_piece_url2': 'format2,
# #                         'data_piece_url3': 'format3,
# #                 },
# #                 'sami_1234': {
# #                         'data_piece_url1': 'format1,
# #                         'data_piece_url2': 'format2,
# #                         'data_piece_url3': 'format3,
# #                 }, ...
# #             }
# #             The urls serve as the primary keys.
# #         """
# #         cart_representation = {}
# #         for item in self.items:
# #             # JSON serialization
# #             cart_representation[ao] = item.to_dict()
# #
# #         return cart_representation
# #
# #     @property
# #     def urls(self):
# #         """
# #         The list of urls.
# #         """
# #         return [item.url for item in self.items]
