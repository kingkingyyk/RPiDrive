from django.views.decorators.http import require_GET
from drive.views.web.shared import spam_protect
from django.http.response import HttpResponse

@require_GET
@spam_protect
def page_not_found(request, **kwargs):
    return HttpResponse('Page not found.', status=404)
