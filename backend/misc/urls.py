from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404
from django.shortcuts import render
from django.template.exceptions import TemplateDoesNotExist
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import re_path


@ensure_csrf_cookie
def index(request: WSGIRequest):
    """Base page view"""
    try:
        return render(request, "index.html")
    except TemplateDoesNotExist:
        raise Http404("Page not found.")  # pylint: disable=raise-missing-form


urlpatterns = [
    re_path(r"^(?:.*)/?$", index),
]
