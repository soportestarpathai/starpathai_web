"""
Servicio para extraer información de documentos (INE, Comprobante de domicilio)
usando imágenes o PDF convertidos a base64 y OpenAI Vision.
"""
import base64
import io
import json
import logging
import re
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

DOC_TYPE_INE = "ine"
DOC_TYPE_COMPROBANTE = "comprobante_domicilio"
DOC_TYPES = (DOC_TYPE_INE, DOC_TYPE_COMPROBANTE)

# Límite de tamaño (5 MB) para evitar cargas excesivas
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp")
ALLOWED_EXT = ALLOWED_IMAGE_EXT + (".pdf",)


def _file_to_base64_image(file_content: bytes, filename: str, content_type: str) -> tuple[str, str] | None:
    """
    Convierte archivo (imagen o PDF) a base64 para enviar a OpenAI Vision.
    Retorna (base64_string, mime_type) o None si falla.
    """
    ext = (filename or "").lower()
    if "." in ext:
        ext = "." + ext.rsplit(".", 1)[-1]
    else:
        ext = ""

    # Imagen directa
    if ext in ALLOWED_IMAGE_EXT or (content_type or "").startswith("image/"):
        b64 = base64.b64encode(file_content).decode("utf-8")
        mime = content_type or "image/jpeg"
        if mime not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
            mime = "image/jpeg"
        return b64, mime

    # PDF -> primera página como imagen
    if ext == ".pdf" or (content_type or "").lower() == "application/pdf":
        try:
            import fitz  # PyMuPDF
        except ImportError:
            try:
                import pypdfium2 as pdfium
                return _pdf_to_base64_pypdfium2(file_content)
            except ImportError:
                logger.warning("Ni PyMuPDF ni pypdfium2 disponibles para convertir PDF a imagen.")
                return None
        doc = fitz.open(stream=file_content, filetype="pdf")
        if len(doc) == 0:
            doc.close()
            return None
        page = doc[0]
        mat = fitz.Matrix(2, 2)  # scale 2x para mejor lectura
        pix = page.get_pixmap(matrix=mat, alpha=False)
        png_bytes = pix.tobytes("png")
        doc.close()
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return b64, "image/png"

    return None


def _pdf_to_base64_pypdfium2(file_content: bytes) -> tuple[str, str] | None:
    """Fallback: convertir PDF con pypdfium2 si PyMuPDF no está."""
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(file_content)
        if doc.get_page_count() == 0:
            doc.close()
            return None
        page = doc.get_page(0)
        pil_image = page.render_topil(scale=2)
        page.close()
        doc.close()
        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        return b64, "image/png"
    except Exception as e:
        logger.warning("pypdfium2 PDF conversion failed: %s", e)
        return None


def _build_prompt(doc_type: str) -> str:
    if doc_type == DOC_TYPE_INE:
        return """Analiza esta imagen de un INE (Credencial para votar de México) y extrae la información en formato JSON.
Devuelve ÚNICAMENTE un objeto JSON válido, sin markdown ni texto adicional, con las siguientes claves (usa null si no se encuentra):
- nombres: string (nombre completo)
- apellido_paterno: string
- apellido_materno: string
- curp: string
- clave_elector: string
- anio_registro: string
- anio_emision: string
- numero_emision_credencial: string
- domicilio: string (dirección completa)
- sexo: string
- seccion: string
- localidad: string
- municipio: string
- estado: string
- vigencia: string
- fecha_nacimiento: string (YYYY-MM-DD si es posible)
- anio_nacimiento: string
"""
    if doc_type == DOC_TYPE_COMPROBANTE:
        return """Analiza esta imagen de un comprobante de domicilio (recibo de luz, agua, gas, teléfono, predial, etc.) y extrae la información en formato JSON.
Devuelve ÚNICAMENTE un objeto JSON válido, sin markdown ni texto adicional, con las siguientes claves (usa null si no se encuentra):
- titular: string (nombre del titular del servicio)
- direccion: string (dirección completa)
- colonia: string
- codigo_postal: string
- ciudad: string
- estado: string
- tipo_servicio: string (luz, agua, gas, teléfono, predial, etc.)
- proveedor: string (CFE, SACMEX, nombre de la empresa, etc.)
- referencia: string (número de servicio o referencia)
- periodo: string (periodo facturado si aplica)
- fecha_emision: string (si se ve)
- monto: string (si se ve)
"""
    return "Extrae la información visible en este documento y devuélvela como JSON."


def _parse_json_from_response(content: str) -> dict | None:
    """Intenta extraer JSON del contenido de la respuesta (puede venir envuelto en ```json)."""
    content = (content or "").strip()
    # Quitar posibles bloques markdown
    for pattern in (r"```(?:json)?\s*([\s\S]*?)```", r"\{[\s\S]*\}"):
        m = re.search(pattern, content)
        if m:
            try:
                json_str = m.group(1) if "```" in pattern else m.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def extract_document_info(
    file_content: bytes,
    filename: str,
    content_type: str,
    doc_type: str,
) -> dict:
    """
    Extrae información del documento usando OpenAI Vision.
    - file_content: bytes del archivo
    - filename: nombre original (para detectar tipo)
    - content_type: MIME type
    - doc_type: "ine" o "comprobante_domicilio"

    Retorna {"ok": True, "data": {...}} o {"ok": False, "error": "mensaje"}
    """
    if doc_type not in DOC_TYPES:
        return {"ok": False, "error": f"Tipo de documento inválido. Use: {', '.join(DOC_TYPES)}"}

    if len(file_content) > MAX_FILE_SIZE:
        logger.warning("document_extraction file too large: %d bytes (max %d)", len(file_content), MAX_FILE_SIZE)
        return {"ok": False, "error": f"Archivo demasiado grande. Máximo {MAX_FILE_SIZE // (1024*1024)} MB"}

    logger.info("document_extraction converting to base64 filename=%s doc_type=%s", filename, doc_type)
    result = _file_to_base64_image(file_content, filename, content_type)
    if not result:
        logger.warning("document_extraction could not convert file to image: %s", filename)
        return {"ok": False, "error": "No se pudo procesar el archivo. Use imagen (JPG, PNG) o PDF."}

    b64, mime = result
    api_key = getattr(settings, "OPENAI_API_KEY_DOCUMENTS", None) or getattr(settings, "OPENAI_API_KEY", None) or ""
    if not api_key.strip():
        return {"ok": False, "error": "OpenAI API no configurada."}

    prompt = _build_prompt(doc_type)
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    # Para visión usar gpt-4o o gpt-4o-mini (ambos tienen visión)
    vision_model = "gpt-4o-mini" if "gpt-4" in model else "gpt-4o-mini"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
            max_tokens=1500,
        )
        content = (response.choices[0].message.content or "").strip()
        data = _parse_json_from_response(content)
        if data is None:
            logger.warning("document_extraction OpenAI response not valid JSON, raw_len=%d", len(content))
            return {"ok": False, "error": "No se pudo interpretar la respuesta como JSON.", "raw": content[:500]}
        logger.info("document_extraction success filename=%s doc_type=%s", filename, doc_type)
        return {"ok": True, "data": data}
    except Exception as e:
        logger.exception("document_extraction OpenAI call failed: %s", e)
        return {"ok": False, "error": str(e)}
