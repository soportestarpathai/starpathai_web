import logging
from django.conf import settings
from django.core.mail import EmailMessage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework import status

logger = logging.getLogger(__name__)

class LandingPage(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "landing/index.html"

    def get(self, request):
        return Response({"titulo": "StarpathAI"})

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        email = (request.data.get("email") or "").strip()
        subject = (request.data.get("subject") or "").strip()
        message = (request.data.get("message") or "").strip()

        errors = {}
        if not name: errors["name"] = "El nombre es obligatorio."
        if not email or "@" not in email: errors["email"] = "Correo inválido."
        if not subject: errors["subject"] = "El asunto es obligatorio."
        if not message: errors["message"] = "El mensaje es obligatorio."

        if errors:
            return Response({"ok": False, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # sanity check envs (en prod te salva)
            if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                return Response({"ok": False, "error": "Email SMTP no configurado."}, status=500)

            msg = EmailMessage(
                subject=f"[Contacto Star Path] {subject}",
                body=(
                    f"Nombre: {name}\n"
                    f"Email: {email}\n"
                    f"Asunto: {subject}\n\n"
                    f"Mensaje:\n{message}\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_TO_EMAIL],
                reply_to=[email],
            )
            msg.send(fail_silently=False)

            return Response({"ok": True}, status=200)

        except Exception as e:
            logger.exception("PROD: Error enviando correo (SMTP).")
            return Response({"ok": False, "error": str(e)}, status=500)
