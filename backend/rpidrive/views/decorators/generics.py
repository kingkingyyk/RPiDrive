import functools
import http
import logging

from typing import Set

from django.http import JsonResponse
from pydantic import ValidationError
from rpidrive.controllers.exceptions import (
    NoPermissionException,
    ObjectNotFoundException,
)

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
            status_code = (
                http.HTTPStatus.BAD_REQUEST
                if known_exc and type(exc) in known_exc
                else http.HTTPStatus.INTERNAL_SERVER_ERROR
            )
            error_msg = str(exc)

            if isinstance(exc, NoPermissionException):
                status_code = http.HTTPStatus.FORBIDDEN
            elif isinstance(exc, ObjectNotFoundException):
                status_code = http.HTTPStatus.NOT_FOUND
            elif isinstance(exc, ValidationError):
                status_code = http.HTTPStatus.BAD_REQUEST
                msg_list = []
                for error in exc.errors():  # pylint: disable=no-member
                    loc_join = ", ".join(error["loc"])
                    msg_list.append(f"{loc_join} -> {error['msg']}")
                error_msg = "\n".join(msg_list)

            return JsonResponse(
                {"error": error_msg},
                status=status_code,
            )

    return wrapper
