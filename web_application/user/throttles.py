from rest_framework import throttling


class RegistrationRateThrottle(throttling.AnonRateThrottle):
    scope = 'register'
