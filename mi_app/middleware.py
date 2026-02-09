"""
Middleware para registrar cada request desde entrada hasta salida (método, path, status, tiempo).
"""
import logging
import time

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
