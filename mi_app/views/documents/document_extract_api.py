"""
API para extracción de información de documentos (INE, Comprobante de domicilio).
Recibe PDF o imagen, convierte a base64 y usa OpenAI Vision para devolver JSON.
"""
from __future__ import annotations

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.throttling import ScopedRateThrottle
from mi_app.authentication import DocumentsAPIKeyAuthentication, IsAPIKeyAuthenticated
from mi_app.services.document_extraction import (
    extract_document_info,
    DOC_TYPE_INE,
    DOC_TYPE_COMPROBANTE,
    DOC_TYPES,
)

logger = logging.getLogger(__name__)


class DocumentExtractAPIView(APIView):
    """
    POST /api/documents/extract/
    Requiere autenticación por API key (header Authorization: Bearer <key> o X-API-Key: <key>).
    - file: PDF o imagen (JPG, PNG, GIF, WEBP)
    - document_type: "ine" | "comprobante_domicilio"

    Respuesta: {"ok": true, "data": {...}} o {"ok": false, "error": "..."}
    """
    authentication_classes = [DocumentsAPIKeyAuthentication]
    permission_classes = [IsAPIKeyAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "documents"
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        logger.info("documents_extract POST request received")
        uploaded = request.FILES.get("file")
        doc_type = (request.data.get("document_type") or request.POST.get("document_type") or "").strip().lower()

        if not uploaded:
            logger.warning("documents_extract missing file")
            return Response(
                {"ok": False, "error": "Falta el archivo. Envía 'file' en multipart/form-data."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not doc_type or doc_type not in DOC_TYPES:
            logger.warning("documents_extract invalid document_type=%s", doc_type or "(vacío)")
            return Response(
                {
                    "ok": False,
                    "error": f"document_type inválido. Use: {DOC_TYPE_INE} o {DOC_TYPE_COMPROBANTE}.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            file_content = uploaded.read()
        except Exception as e:
            logger.warning("documents_extract read file failed: %s", e)
            return Response(
                {"ok": False, "error": "No se pudo leer el archivo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filename = getattr(uploaded, "name", "") or "document"
        content_type = getattr(uploaded, "content_type", "") or ""
        logger.info("documents_extract processing file=%s doc_type=%s size=%d bytes", filename, doc_type, len(file_content))

        result = extract_document_info(
            file_content=file_content,
            filename=filename,
            content_type=content_type,
            doc_type=doc_type,
        )

        if result.get("ok"):
            logger.info("documents_extract success file=%s doc_type=%s", filename, doc_type)
            return Response(result, status=status.HTTP_200_OK)
        logger.warning("documents_extract failed file=%s doc_type=%s error=%s", filename, doc_type, result.get("error", ""))
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
