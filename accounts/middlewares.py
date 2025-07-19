from django.utils.deprecation import MiddlewareMixin

from resolve_erp import settings
from .task import create_endpoint_access_log


class EndpointAccessLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if (
            not settings.DISABLE_ENDPOINT_ACCESS_LOG
            and request.method
            in [
                "GET",
                "POST",
                "PUT",
                "DELETE",
            ]
            and request.path.startswith(
                (
                    "/api/projects/",
                    "/api/users/",
                    "/api/sales/",
                )
            )
        ):
            request_data = {
                "method": request.method,
                "path": request.path,
                "user_id": (
                    request.user.id
                    if hasattr(request, "user") and request.user.is_authenticated
                    else None
                ),
                "remote_addr": request.META.get("HTTP_X_REAL_IP")
                or request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
                or request.META.get("REMOTE_ADDR", "unknown"),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            }
            create_endpoint_access_log.delay(request_data)
        return None
