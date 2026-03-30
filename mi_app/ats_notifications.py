"""
Helper para crear notificaciones ATS (in-app) y enviar email al correo de notificaciones.
"""
import html
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)

# Máximo de notificaciones por cliente; las más antiguas se eliminan para no inflar el conteo
NOTIFICATIONS_MAX_PER_CLIENT = 200


def notify_ats_client(client, notification_type, title, message="", link="", request=None):
    """
    Crea una notificación in-app para el cliente y, si tiene notification_email
    configurado, envía un correo.
    Mantiene solo las últimas NOTIFICATIONS_MAX_PER_CLIENT por cliente (borra las más viejas).

    - client: ATSClient
    - notification_type: ATSNotification.TYPE_* (submission, candidate, plan, cvs_limit)
    - title: str
    - message: str (opcional)
    - link: str (URL absoluta o path; si es path se puede construir con request)
    - request: HttpRequest opcional, para construir URL absoluta en el email
    """
    from mi_app.models import ATSNotification, ATSClientEmailConfig

    notification = ATSNotification.objects.create(
        client=client,
        type=notification_type,
        title=title,
        message=message or "",
        link=link or "",
        read=False,
    )

    # Limpieza: mantener solo las últimas N por cliente para que el conteo no explote
    ids_to_keep = list(
        ATSNotification.objects.filter(client=client)
        .order_by("-created_at")
        .values_list("pk", flat=True)[:NOTIFICATIONS_MAX_PER_CLIENT]
    )
    if len(ids_to_keep) >= NOTIFICATIONS_MAX_PER_CLIENT:
        ATSNotification.objects.filter(client=client).exclude(pk__in=ids_to_keep).delete()

    try:
        config = getattr(client, "email_config", None)
        if not config:
            config = ATSClientEmailConfig.objects.filter(client=client).first()
        if not config or not getattr(config, "notification_email", None):
            return notification

        to_email = config.notification_email.strip()
        if not to_email:
            return notification

        # Construir URL absoluta para el enlace en el correo
        if link and request and not link.startswith("http"):
            full_url = request.build_absolute_uri(link)
        elif link:
            full_url = link
        else:
            full_url = ""
        if full_url and request:
            dashboard = request.build_absolute_uri(reverse("ats_dashboard"))
        else:
            dashboard = ""

        email_body = f"{title}\n\n"
        if message:
            email_body += f"{message}\n\n"
        if full_url:
            email_body += f"Ver: {full_url}\n"
        elif dashboard:
            email_body += f"Panel Órbita: {dashboard}\n"

        send_mail(
            subject=f"[Órbita] {title}",
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=True,
        )
    except Exception as e:
        logger.warning("ATS notify email failed: %s", e)

    return notification


def notify_support_plan_change(user, ats_client, old_plan_id, new_plan_id):
    """
    Envía un correo a soporte (soporte@starpathai.mx) cuando un cliente solicita
    cambio de plan. Soporte debe validar, gestionar el pago externo y luego activar
    el plan desde el administrador de Django (no se aplica el cambio automáticamente).

    - user: User (request.user)
    - ats_client: ATSClient o None
    - old_plan_id: str (ej. "FREE")
    - new_plan_id: str (ej. "PRO")
    """
    to_email = getattr(settings, "ATS_SUPPORT_EMAIL", "soporte@starpathai.mx")
    if not to_email or not to_email.strip():
        return
    to_email = to_email.strip()

    plan_names = {"FREE": "Gratuito", "PRO": "Pro", "ENTERPRISE": "Enterprise"}
    old_name = plan_names.get(old_plan_id, old_plan_id)
    new_name = plan_names.get(new_plan_id, new_plan_id)

    company = html.escape(ats_client.company_name if ats_client else "—")
    contact = html.escape(ats_client.contact_name if ats_client else "—")
    phone_raw = (ats_client.contact_phone or "").strip() if ats_client else ""
    phone_display = phone_raw if phone_raw else "—"
    phone = html.escape(phone_raw) if phone_raw else "—"
    user_email_raw = getattr(user, "email", "") or "—"
    user_email = html.escape(user_email_raw)

    subject = "[Órbita] Solicitud de cambio de plan - validar y activar desde admin"
    body_plain = f"""Un cliente ha solicitado cambio de plan en Órbita. El plan NO se ha cambiado aún.

Acción requerida:
1. Validar la solicitud.
2. Gestionar el pago externo con el cliente.
3. Una vez cobrado, activar el nuevo plan desde el administrador de Django (Suscripciones Órbita / Subscription).

Datos del cliente:
- Empresa: {company}
- Contacto: {contact}
- Correo: {user_email_raw}
- Teléfono: {phone_display}

Plan actual: {old_name} ({old_plan_id})
Plan solicitado: {new_name} ({new_plan_id})
"""
    old_name = html.escape(plan_names.get(old_plan_id, old_plan_id))
    new_name = html.escape(plan_names.get(new_plan_id, new_plan_id))
    body_html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; font-family: 'Segoe UI', Roboto, sans-serif; background:#f0f4f8; padding: 24px;">
  <div style="max-width: 520px; margin: 0 auto; background:#fff; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden;">
    <div style="background: linear-gradient(135deg, #0B1C2D 0%, #122d47 100%); color: #fff; padding: 20px 24px;">
      <h1 style="margin: 0; font-size: 1.25rem; font-weight: 700;">Solicitud de cambio de plan</h1>
      <p style="margin: 6px 0 0; font-size: 0.9rem; opacity: 0.9;">Órbita — Validar y activar desde admin</p>
    </div>
    <div style="padding: 24px;">
      <p style="margin: 0 0 20px; color: #444; line-height: 1.5;">Un cliente ha solicitado cambio de plan. El plan <strong>no</strong> se ha cambiado aún.</p>
      <div style="background: #f8fafc; border-left: 4px solid #00C4C9; padding: 14px 16px; margin-bottom: 20px; border-radius: 0 10px 10px 0;">
        <p style="margin: 0 0 8px; font-weight: 600; color: #0B1C2D;">Acción requerida:</p>
        <ol style="margin: 0; padding-left: 20px; color: #444;">
          <li>Validar la solicitud.</li>
          <li>Gestionar el pago externo con el cliente.</li>
          <li>Una vez cobrado, activar el nuevo plan desde el administrador (Suscripciones Órbita).</li>
        </ol>
      </div>
      <table style="width: 100%; border-collapse: collapse; font-size: 0.95rem;">
        <tr><td style="padding: 10px 0; border-bottom: 1px solid #eee; color: #666;">Empresa</td><td style="padding: 10px 0; border-bottom: 1px solid #eee; font-weight: 600; color: #0B1C2D;">{company}</td></tr>
        <tr><td style="padding: 10px 0; border-bottom: 1px solid #eee; color: #666;">Contacto</td><td style="padding: 10px 0; border-bottom: 1px solid #eee; font-weight: 600;">{contact}</td></tr>
        <tr><td style="padding: 10px 0; border-bottom: 1px solid #eee; color: #666;">Correo</td><td style="padding: 10px 0; border-bottom: 1px solid #eee;"><a href="mailto:{user_email_raw}">{user_email}</a></td></tr>
        <tr><td style="padding: 10px 0; border-bottom: 1px solid #eee; color: #666;">Teléfono</td><td style="padding: 10px 0; border-bottom: 1px solid #eee;">{f'<a href="tel:{phone_raw}" style="color:#00C4C9; text-decoration:none;">{phone}</a>' if phone_raw else phone}</td></tr>
      </table>
      <div style="margin-top: 24px; display: flex; gap: 16px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 140px; background: #f8fafc; padding: 14px; border-radius: 10px;">
          <p style="margin: 0 0 4px; font-size: 0.8rem; color: #666; text-transform: uppercase;">Plan actual</p>
          <p style="margin: 0; font-weight: 700; color: #0B1C2D;">{old_name} <span style="font-weight: 400; color: #888;">({old_plan_id})</span></p>
        </div>
        <div style="flex: 1; min-width: 140px; background: rgba(0,196,201,0.1); padding: 14px; border-radius: 10px; border: 1px solid rgba(0,196,201,0.3);">
          <p style="margin: 0 0 4px; font-size: 0.8rem; color: #00a8ad;">Plan solicitado</p>
          <p style="margin: 0; font-weight: 700; color: #0B1C2D;">{new_name} <span style="font-weight: 400; color: #888;">({new_plan_id})</span></p>
        </div>
      </div>
    </div>
    <div style="padding: 14px 24px; background: #f8fafc; font-size: 0.8rem; color: #666; border-top: 1px solid #eee;">Órbita — Star Path</div>
  </div>
</body>
</html>
"""
    try:
        send_mail(
            subject=subject,
            message=body_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=body_html,
            fail_silently=True,
        )
    except Exception as e:
        logger.warning("ATS notify_support_plan_change failed: %s", e)


def notify_support_account_deletion_request(ats_client):
    """
    Envía un correo a soporte cuando un cliente solicita la baja de su cuenta.
    Soporte puede proceder a desactivar o eliminar los datos desde el admin.
    """
    to_email = getattr(settings, "ATS_SUPPORT_EMAIL", "soporte@starpathai.mx")
    if not to_email or not to_email.strip():
        return
    to_email = to_email.strip()
    company = html.escape(ats_client.company_name if ats_client else "—")
    contact = html.escape(ats_client.contact_name or "—")
    user_email = html.escape(getattr(ats_client.user, "email", "") or "—")
    subject = "[Órbita] Solicitud de baja de cuenta"
    body_plain = f"""Un cliente ha solicitado la baja de su cuenta en Órbita.

Empresa: {company}
Contacto: {contact}
Correo: {user_email}

Proceder con la baja/eliminación desde el administrador si corresponde.
"""
    body_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="font-family: sans-serif; padding: 20px;">
<h1 style="font-size: 1.2rem;">Solicitud de baja de cuenta</h1>
<p>Un cliente ha solicitado la baja de su cuenta en Órbita.</p>
<table style="border-collapse: collapse;">
<tr><td style="padding: 6px 12px 6px 0; font-weight: 700;">Empresa</td><td>{company}</td></tr>
<tr><td style="padding: 6px 12px 6px 0; font-weight: 700;">Contacto</td><td>{contact}</td></tr>
<tr><td style="padding: 6px 12px 6px 0; font-weight: 700;">Correo</td><td>{user_email}</td></tr>
</table>
<p style="margin-top: 20px; color: #666;">Proceder con la baja/eliminación desde el administrador si corresponde.</p>
</body></html>"""
    try:
        send_mail(
            subject=subject,
            message=body_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=body_html,
            fail_silently=True,
        )
    except Exception as e:
        logger.warning("ATS notify_support_account_deletion_request failed: %s", e)


def send_email_to_candidate(client, candidate, email_type, custom_message=None):
    """
    Envía un correo al candidato: "apto para reclutar" o "no seleccionado" (rechazo).
    - client: ATSClient (para from_email desde config)
    - candidate: Candidate (debe tener email)
    - email_type: "apto" o "rechazo"
    - custom_message: str opcional para personalizar el cuerpo.
    Retorna True si se envió, False si no (sin email, sin SMTP, etc.).
    """
    to_email = (candidate.email or "").strip()
    if not to_email or "@" not in to_email:
        return False
    config = getattr(client, "email_config", None)
    if not config:
        from mi_app.models import ATSClientEmailConfig
        config = ATSClientEmailConfig.objects.filter(client=client).first()
    if not config:
        logger.warning("send_email_to_candidate: sin configuración de correo para client=%s", getattr(client, "pk", None))
        return False

    smtp_host = (getattr(config, "smtp_host", "") or "").strip()
    smtp_user = (getattr(config, "smtp_user", "") or "").strip()
    smtp_password = (getattr(config, "smtp_password_encrypted", "") or "").strip()
    smtp_port = int(getattr(config, "smtp_port", 587) or 587)
    smtp_use_tls = bool(getattr(config, "smtp_use_tls", True))
    if not smtp_host or not smtp_user or not smtp_password:
        logger.warning(
            "send_email_to_candidate: SMTP incompleto para client=%s (host/user/password requeridos)",
            getattr(client, "pk", None),
        )
        return False

    from_email = (getattr(config, "company_from_email", "") or "").strip() or smtp_user
    from_name = (getattr(config, "company_from_name", "") or "").strip() or client.company_name or "Órbita"
    from_header = f"{from_name} <{from_email}>" if from_name else from_email
    candidate_name = (candidate.name or "Candidato/a").strip()
    if email_type == "apto":
        subject = "Tu perfil es apto para el proceso de reclutamiento"
        body = custom_message or (
            f"Hola {candidate_name},\n\n"
            "Te informamos que tras revisar tu perfil y CV, has sido considerado/a apto/a para continuar en el proceso de reclutamiento.\n\n"
            "Nos pondremos en contacto contigo pronto para los siguientes pasos.\n\n"
            "Saludos cordiales."
        )
    else:
        subject = "Resultado de tu postulación"
        body = custom_message or (
            f"Hola {candidate_name},\n\n"
            "Agradecemos tu interés y el tiempo dedicado a postularte. Tras revisar los perfiles, en esta ocasión hemos decidido continuar con otros candidatos.\n\n"
            "Te deseamos éxito en tu búsqueda y te invitamos a estar atento/a a futuras vacantes.\n\n"
            "Saludos cordiales."
        )

    is_apto = email_type == "apto"
    status_badge = "Perfil apto para continuar" if is_apto else "Resultado de postulación"
    status_color = "#10b981" if is_apto else "#ef4444"
    company_name_html = html.escape(from_name or "Órbita")
    candidate_name_html = html.escape(candidate_name)
    vacancy_title = ""
    if getattr(candidate, "vacancy", None):
        vacancy_title = (getattr(candidate.vacancy, "title", "") or "").strip()
    vacancy_html = html.escape(vacancy_title) if vacancy_title else ""

    body_html_lines = "<br>".join(html.escape(line) for line in body.splitlines())
    email_body_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:24px; background:#f3f6fb; font-family:'Segoe UI', Roboto, Arial, sans-serif; color:#243447;">
  <div style="max-width:640px; margin:0 auto; background:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 8px 24px rgba(11,28,45,0.08);">
    <div style="background:linear-gradient(135deg, #0b1c2d 0%, #16324f 100%); padding:24px 26px;">
      <p style="margin:0; color:#9fd9ff; font-size:12px; letter-spacing:.08em; text-transform:uppercase;">Órbita • Comunicación de reclutamiento</p>
      <h1 style="margin:8px 0 0; color:#ffffff; font-size:22px; line-height:1.25;">{html.escape(subject)}</h1>
      <span style="display:inline-block; margin-top:14px; background:{status_color}; color:#fff; padding:7px 12px; border-radius:999px; font-size:12px; font-weight:700;">{status_badge}</span>
    </div>
    <div style="padding:24px 26px;">
      <p style="margin:0 0 14px; font-size:15px; line-height:1.6;">Hola <strong>{candidate_name_html}</strong>,</p>
      <div style="font-size:15px; line-height:1.65; color:#34495e; margin-bottom:18px;">{body_html_lines}</div>
      <div style="background:#f8fbff; border:1px solid #e6eef8; border-radius:12px; padding:14px 16px; margin-top:10px;">
        <p style="margin:0 0 6px; color:#5a6a7b; font-size:12px; text-transform:uppercase; letter-spacing:.06em;">Empresa</p>
        <p style="margin:0; font-size:15px; font-weight:700; color:#0b1c2d;">{company_name_html}</p>
        {f'<p style="margin:10px 0 0; font-size:14px; color:#44566b;"><strong>Vacante:</strong> {vacancy_html}</p>' if vacancy_html else ''}
      </div>
    </div>
    <div style="padding:14px 26px; border-top:1px solid #ecf1f7; background:#fafcff;">
      <p style="margin:0; color:#7a8794; font-size:12px;">Este mensaje fue enviado desde Órbita. Si tienes dudas, responde a este correo.</p>
    </div>
  </div>
</body>
</html>"""
    try:
        from django.core.mail.backends.smtp import EmailBackend
        connection = EmailBackend(
            host=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            use_tls=smtp_use_tls,
            timeout=getattr(settings, "EMAIL_TIMEOUT", 10),
            fail_silently=False,
        )
        send_mail(
            subject=f"[{from_name}] {subject}",
            message=body,
            from_email=from_header,
            recipient_list=[to_email],
            html_message=email_body_html,
            fail_silently=False,
            connection=connection,
        )
        return True
    except Exception as e:
        logger.warning("send_email_to_candidate failed: %s", e)
        return False
