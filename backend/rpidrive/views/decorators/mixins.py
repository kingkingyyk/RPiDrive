import http

from django.conf import settings
from django.core.cache import cache
from django.http.response import HttpResponse, JsonResponse


class BruteForceProtectMixin:
    """Brute force protect mixin"""

    _DEFAULT_HEADER = "REMOTE_ADDR"

    @staticmethod
    def construct_key(ip_add: str) -> str:
        """Construct cache key"""
        return f"bruteforce.{ip_add}"

    @staticmethod
    def reset():
        """Reset data"""
        cache.delete_pattern(BruteForceProtectMixin.construct_key("*"))

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """Handle dispatch"""
        key = None
        if settings.ROOT_CONFIG.security.block_spam:
            remote_addr = None
            if (
                settings.ROOT_CONFIG.reverse_proxy
                and settings.ROOT_CONFIG.reverse_proxy.ip_header
            ):
                remote_addr = request.META.get(
                    settings.ROOT_CONFIG.reverse_proxy.ip_header
                ).split(",")[0]
            else:
                remote_addr = request.META.get(self._DEFAULT_HEADER)
            key = BruteForceProtectMixin.construct_key(remote_addr)
            if (
                cache.has_key(key)
                and cache.get(key) >= settings.ROOT_CONFIG.security.block_trigger
            ):
                return JsonResponse(
                    {
                        "error": "Request blocked temporarily due to too many failed attempts!"
                    },
                    status=http.HTTPStatus.FORBIDDEN,
                )

        response = super().dispatch(request, *args, **kwargs)
        if key:
            if response.status_code == http.HTTPStatus.OK:
                cache.delete(key)
            else:
                if cache.has_key(key):
                    cache.incr(key, 1)
                    cache.touch(key, settings.ROOT_CONFIG.security.block_duration)
                else:
                    cache.set(
                        key,
                        1,
                        timeout=settings.ROOT_CONFIG.security.block_duration,
                    )
        return response
