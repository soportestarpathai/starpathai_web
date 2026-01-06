from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import escape
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework import status


class LandingPage(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "landing/index.html"

    def get(self, request):
        return Response({"titulo": "StarpathAI"})

    def post(self, request):
        # Tomamos datos del form (POST tradicional o fetch/ajax)
        name = (request.data.get("name") or "").strip()
        email = (request.data.get("email") or "").strip()
        subject = (request.data.get("subject") or "").strip()
        message = (request.data.get("message") or "").strip()

        # Validación básica
        errors = {}
        if not name:
            errors["name"] = "El nombre es obligatorio."
        if not email or "@" not in email:
            errors["email"] = "El correo es obligatorio y debe ser válido."
        if not subject:
            errors["subject"] = "El asunto es obligatorio."
        if not message:
            errors["message"] = "El mensaje es obligatorio."

        if errors:
            # Si es llamada AJAX, devolvemos JSON
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return Response({"ok": False, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
            # Si es submit normal, re-render con errores
            return Response({"titulo": "StarpathAI", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # Construimos el correo
        safe_name = escape(name)
        safe_email = escape(email)
        safe_subject = escape(subject)

        mail_subject = f"[Contacto Star Path] {safe_subject}"
        mail_body = (
            f"Nuevo mensaje desde el formulario:\n\n"
            f"Nombre: {safe_name}\n"
            f"Email: {safe_email}\n"
            f"Asunto: {safe_subject}\n\n"
            f"Mensaje:\n{message}\n"
        )

        try:
            send_mail(
                subject=mail_subject,
                message=mail_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_TO_EMAIL],
                fail_silently=False,
                reply_to=[email],  # Para responder directo al cliente
            )
        except Exception as e:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return Response(
                    {"ok": False, "error": "No se pudo enviar el mensaje. Intenta más tarde."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(
                {"titulo": "StarpathAI", "send_error": "No se pudo enviar el mensaje. Intenta más tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # OK
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return Response({"ok": True})

        # Si prefieres submit normal, puedes retornar la misma página con flag:
        return Response({"titulo": "StarpathAI", "sent": True})