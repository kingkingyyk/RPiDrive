import functools
import http
import logging

from typing import Set

from django.http import JsonResponse

logger = logging.getLogger(__name__)


def handle_exceptions(function=None, known_exc: Set = None) -> JsonResponse:
    """Handle exceptions throw by func"""
    if not function:
        return functools.partial(handle_exceptions, known_exc=known_exc)

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.exception("Caught error in handle_exceptions.")
            status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
            if known_exc and type(exc) in known_exc:
                status_code = http.HTTPStatus.BAD_REQUEST
            return JsonResponse(
                {"error": str(exc)},
                status=status_code,
            )

    return wrapper
