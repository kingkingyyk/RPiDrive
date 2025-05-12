from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.exceptions import NoPermissionException
from rpidrive.controllers.job import (
    JobNotFoundException,
    cancel_job,
)
from rpidrive.views.decorators.generics import handle_exceptions


class JobCancelView(LoginRequiredMixin, View):
    """Job cancel view"""

    @handle_exceptions(
        known_exc={
            NoPermissionException,
            JobNotFoundException,
        }
    )
    def post(self, request, job_id: int, *_args, **_kwargs) -> JsonResponse:
        """Handle GET response"""
        cancel_job(request.user, job_id)
        return JsonResponse({})
