import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework import status

logger = logging.getLogger(__name__)

CONTACT_EMAIL_TEMPLATE_HTML = "email/contact_form.html"


class LandingPage(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "landing/index.html"

    def get(self, request):
        logger.info("landing_get inicio")
        try:
            out = Response({"titulo": "StarpathAI"})
            logger.info("landing_get fin ok")
            return out
        except Exception as e:
            logger.exception("landing_get error: %s", e)
            raise

    def post(self, request):
        logger.info("landing_contact_post inicio")
        name = (request.data.get("name") or "").strip()
        email = (request.data.get("email") or "").strip()
        subject = (request.data.get("subject") or "").strip()
        message = (request.data.get("message") or "").strip()

        errors = {}
        if not name:
            errors["name"] = "El nombre es obligatorio."
        if not email or "@" not in email:
            errors["email"] = "Correo inválido."
        if not subject:
            errors["subject"] = "El asunto es obligatorio."
        if not message:
            errors["message"] = "El mensaje es obligatorio."

        if errors:
            logger.warning("landing_contact_post validación fallida errors=%s", errors)
            return Response({"ok": False, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                logger.error("landing_contact_post EMAIL SMTP no configurado (env)")
                return Response(
                    {"ok": False, "error": "Email SMTP no configurado."},
                    status=500,
                )

            to_list = getattr(settings, "CONTACT_TO_EMAILS", None) or [
                getattr(settings, "CONTACT_TO_EMAIL", None),
            ]
            to_list = [e for e in to_list if e]

            plain_body = (
                f"Nombre: {name}\n"
                f"Email: {email}\n"
                f"Asunto: {subject}\n\n"
                f"Mensaje:\n{message}\n"
            )
            html_body = render_to_string(
                CONTACT_EMAIL_TEMPLATE_HTML,
                {"name": name, "email": email, "subject": subject, "message": message},
            )

            msg = EmailMultiAlternatives(
                subject=f"[Contacto Star Path] {subject}",
                body=plain_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=to_list,
                reply_to=[email],
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send(fail_silently=False)

            logger.info("landing_contact_post correo enviado ok to=%s", to_list)
            return Response({"ok": True}, status=200)

        except Exception as e:
            logger.exception("landing_contact_post error enviando correo (SMTP): %s", e)
            return Response({"ok": False, "error": str(e)}, status=500)
