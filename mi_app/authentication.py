"""
Autenticación por API key para endpoints (documentos, etc.).
El cliente envía la clave en header: Authorization: Bearer <key> o X-API-Key: <key>
"""
import logging

from django.conf import settings
from rest_framework import authentication, exceptions
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class DocumentsAPIKeyAuthentication(authentication.BaseAuthentication):
    """
    Autenticación por API key para el endpoint de extracción de documentos.
    Acepta la clave en:
      - Authorization: Bearer <api_key>
      - X-API-Key: <api_key>
    """
    keyword = "Bearer"
    header_api_key = "X-API-Key"

    def authenticate(self, request):
        api_key_expected = getattr(settings, "DOCUMENTS_API_KEY", None) or ""

        if not api_key_expected.strip():
            logger.error("DocumentsAPIKey DOCUMENTS_API_KEY not configured")
            raise exceptions.AuthenticationFailed(
                "El endpoint de documentos no está configurado. Contacta al administrador."
            )

        # 1) Intentar header Authorization: Bearer <key>
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0] == self.keyword:
                key = parts[1].strip()
                if key and key == api_key_expected:
                    return (None, key)  # DRF espera (user, auth) o None

        # 2) Intentar header X-API-Key
        api_key = request.META.get("HTTP_X_API_KEY", "").strip()
        if api_key and api_key == api_key_expected:
            return (None, api_key)

        logger.warning("DocumentsAPIKey auth failed: invalid or missing key")
        raise exceptions.AuthenticationFailed(
            "Clave de API inválida o faltante. Envía Authorization: Bearer <key> o X-API-Key: <key>."
        )


class IsAPIKeyAuthenticated(BasePermission):
    """Permite acceso cuando la autenticación por API key fue exitosa (request.auth está definido)."""

    def has_permission(self, request, view):
        return request.auth is not None
