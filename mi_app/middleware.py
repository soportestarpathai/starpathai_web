"""
Middleware para registrar cada request desde entrada hasta salida (método, path, status, tiempo).
"""
import logging
import time
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Log al inicio del request y al terminar con método, path, status y duración."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        method = request.method
        path = request.path or request.get_full_path()
        logger.info("request_start method=%s path=%s", method, path)

        response = self.get_response(request)

        duration_ms = (time.perf_counter() - start) * 1000
        status = getattr(response, "status_code", None)
        logger.info(
            "request_end method=%s path=%s status=%s duration_ms=%.2f",
            method,
            path,
            status,
            duration_ms,
        )
        return response


class ATSStaffAdminRedirectMiddleware:
    """
    Si un usuario staff (sin perfil ats_client) entra a rutas del dashboard cliente,
    redirige al panel de administración ATS para evitar mezcla de vistas.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""
        user = getattr(request, "user", None)

        if (
            user
            and user.is_authenticated
            and user.is_staff
            and not getattr(user, "ats_client", None)
            and path.startswith("/ats/plataforma/dashboard")
        ):
            return redirect("ats_admin_dashboard")

        return self.get_response(request)
