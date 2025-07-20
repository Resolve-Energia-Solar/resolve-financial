from accounts.task import create_endpoint_access_log


class AccessLogMixin:
    def finalize_response(self, request, response, *args, **kwargs):
        user_id = request.user.id if request.user.is_authenticated else None
        data = {
            "user_id": user_id,
            "path": request.path,
            "method": request.method,
            "ip": (
                request.META.get("HTTP_X_REAL_IP")
                or request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
                or request.META.get("REMOTE_ADDR", "unknown")
            ),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        }
        create_endpoint_access_log.delay(data)
        return super().finalize_response(request, response, *args, **kwargs)
