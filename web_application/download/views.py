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


# class DownloadUnauthenticated(generics.CreateAPIView):
#     """
#     Download products for the data browser if user is unauthenticated (does not save)
#     """
#     class DownloadCreateRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
#         template = 'download/download-create.html'
#     serializer_class = download.serializers.DownloadCreateSerializer
#     permission_classes = [permissions.AllowAny]
#     breadcrumb_list = []
#     renderer_classes = (DownloadCreateRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
#
#     def get_queryset(self):
#         """
#         Download queryset filtered by current user
#         """
#         user = self.request.user
#         return download.models.Download.objects.filter(owner=user).order_by('-updated')
#
#     def perform_create(self, serializer):
#         serializer.save(owner=self.request.user)
#
#     def get(self, request, format=None):
#         """
#         Return the blank form for a POST request
#         """
#         self.breadcrumb_list = ['Download']
#         return Response()



class DownloadCreateView(generics.CreateAPIView):
    """
    Download Viewset. Create new download request, view download history (if authenticated),
    re-issue a download on a particular retrieve.
    """
    class DownloadCreateRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'download/download-create.html'
    serializer_class = download.serializers.DownloadCreateSerializer
    permission_classes = [permissions.AllowAny]
    breadcrumb_list = []
    renderer_classes = (DownloadCreateRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def create(self, request, *args, **kwargs):
        # If logged in, save the serialized data
        if self.request.auth is not None:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            download_data = serializer.validated_data
            print(download_data)
            return Response(data={"download_link": "/asvo/temporary/link/", "download_data": download_data}, status=status.HTTP_200_OK)

    def get_queryset(self):
        """
        Download queryset filtered by current user
        """
        if self.request.auth is not None:
            print('authenticated')
            user = self.request.user
            return download.models.Download.objects.filter(owner=user).order_by('-updated')
        else:
            return download.models.Download.objects.none()

    def perform_create(self, serializer):
        # If logged in, save the serialized data (either way, issue the download here)
        # TODO combine with Andy's code for download
        if self.request.auth is not None:
            serializer.save(owner=self.request.user)
        else:
            raise Exception

    def get(self, request, format=None):
        """
        Return the blank form for a POST request
        """
        self.breadcrumb_list = ['Download']
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

        def get_context(self, data, accepted_media_type, renderer_context):
            context = super().get_context(data, accepted_media_type, renderer_context)
            context['total_count'] = 22
            return context

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
    breadcrumb_list = ['Download History', 'Download ']

    class DownloadRetrieveDestroyRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'download/download-retrieve.html'

    renderer_classes = (DownloadRetrieveDestroyRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def get_queryset(self):
        """
        Download queryset filtered by current user
        """
        user = self.request.user
        return download.models.Download.objects.filter(owner=user).order_by('-updated')


class StorageViewSet(viewsets.GenericViewSet,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     mixins.UpdateModelMixin):
    """
    This is the temporary storage we can use to push items to (using a Service on the angular download
    - switch getItems from cookie to this)
    The download is currently writing large amounts of data into the cookie to manage AND prettify it.
     Move this over to sessions once we allow non-authenticated users to make queries and download data
    """

    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = (restapi_app.renderers.ExtendBrowsableAPIRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    serializer_class = download.serializers.StorageSerializer

    def get_queryset(self):
        """
        Returns:
        """
        user = self.request.user
        return download.models.Storage.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SessionView(views.APIView):
    """ A route for updating the user's session. This seems like the easiest and DRY-est way to
    implement access to session storage throughout the site, without implmenting a
    post-method per view. Instead, the session data is updated if it exists on the request object. """

    permission_classes = [permissions.AllowAny]
    renderer_classes = (restapi_app.renderers.ExtendBrowsableAPIRenderer, renderers.JSONRenderer)
    serializer_class = download.serializers.SessionSerializer

    def get(self, request, format=None):
        # Read data from the session and return it to user
        download_data = {}

        if "download_data" in request.session:
            download_data = request.session['download_data']
        else:
            # set up the download_data obj for a new session
            request.session['download_data'] = {}

        # return the session data for sanity check now
        return Response({"download_data": download_data})

    def put(self, request, format=None):

        if "download_data" in request.data:
            print(request.data["download_data"])
            serializer = download.serializers.SessionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            print('hi')
            print(serializer.validated_data['download_data'])

            validated_data = serializer.validated_data['download_data']
            # Even if the request session for download_data exists, overwrite it
            # with the new data.
            request.session['download_data'] = validated_data

            return Response({"download_data": validated_data})
        else:
            return Response({"download_data": {}})



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
