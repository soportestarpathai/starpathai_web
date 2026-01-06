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

            return Response({"ok": True}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Error enviando correo")
            return Response(
                {"ok": False, "error": "No se pudo enviar el mensaje. Intenta más tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
