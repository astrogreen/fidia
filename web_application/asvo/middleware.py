"""
This module provides very simple Django middleware that sleeps on every request.
This is useful when you want to simulate slow response times (as might be
encountered, say, on a cell network).
To use, add this middleware, and add a value for SLEEP_TIME to your settings.
Possible future feature: Look for an X-Django-Sleep header on each request,
to let the client specify per-request sleep time.
"""

import time

import django.conf
import django.core.exceptions


class SleepMiddleware(object):

    def __init__(self):
        self.sleep_time = getattr(django.conf.settings, "SLEEP_TIME", 0)
        if not isinstance(self.sleep_time, (int, float)) or self.sleep_time <= 0:
            raise django.core.exceptions.MiddlewareNotUsed

    def process_request(self, request):
        sleeptime = 0
        http_origin = request.META.get("HTTP_ORIGIN", None)
        if http_origin is not None:
            # external request, set sleep time to mock slow connection
            # to API
            print('Mocking slow connection (1s lag)')
            sleeptime = self.sleep_time

        time.sleep(sleeptime)
