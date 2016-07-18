from rest_framework import renderers
import restapi_app.renderers


class UserProfileBrowsableAPIRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
    template = 'user/profile/profile.html'
