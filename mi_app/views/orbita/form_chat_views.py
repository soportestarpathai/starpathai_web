"""
Vistas para el chat conversacional de Órbita.
- FormChatPageView: renderiza la interfaz de chat pública.
- FormChatStartAPI / FormChatAnswerAPI: endpoints AJAX para manejar la sesión.
- FormChatSessionsView: vista para el reclutador (historial de sesiones en tiempo real).
- FormChatSessionDetailAPI: endpoint AJAX para polling del progreso de una sesión.
"""
import json
import logging
import uuid as _uuid
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from mi_app.models import (
    ATSForm,
    ATSFormField,
    ATSFormSubmission,
    ATSFormSubmissionFile,
    ATSNotification,
    FormChatSession,
)
from mi_app.orbita_notifications import notify_orbita_client

logger = logging.getLogger(__name__)


def _build_steps(orbita_form):
    """Construye la lista ordenada de pasos del chat a partir de los campos del formulario."""
    steps = []
    for field in orbita_form.fields.all().order_by("order", "id"):
        options = []
        if getattr(field, "option_values", None):
            options = [str(v).strip() for v in field.option_values if str(v).strip()]
        steps.append({
            "id": f"field_{field.id}",
            "label": field.label,
            "type": field.field_type,
            "required": field.required,
            "placeholder": field.placeholder or "",
            "options": options,
        })

    has_email_field = any(s["type"] == ATSFormField.FIELD_EMAIL for s in steps)
    if orbita_form.request_email and not has_email_field:
        steps.append({
            "id": "submitter_email",
            "label": "Correo electrónico",
            "type": "email",
            "required": True,
            "placeholder": "tu@email.com",
        })

    if orbita_form.request_cv:
        steps.append({
            "id": "cv_file",
            "label": "Sube tu CV",
            "type": "file",
            "required": False,
            "placeholder": "",
        })

    return steps


class FormChatPageView(View):
    """Renderiza la interfaz de chat pública para un formulario."""
    template_name = "orbita/form_chat.html"

    def get(self, request, uuid):
        orbita_form = get_object_or_404(ATSForm, uuid=uuid, is_active=True)
        steps = _build_steps(orbita_form)
        return render(request, self.template_name, {
            "orbita_form": orbita_form,
            "steps_json": json.dumps(steps),
            "total_steps": len(steps),
        })


class FormChatStartAPI(View):
    """POST: inicia una nueva sesión de chat. Devuelve session_uuid y los pasos."""

    def post(self, request, uuid):
        orbita_form = get_object_or_404(ATSForm, uuid=uuid, is_active=True)

        ip = request.META.get("REMOTE_ADDR", "") or "unknown"
        cache_key = f"orbita_chat_start:{ip}:{uuid}"
        count = cache.get(cache_key, 0)
        max_count = getattr(settings, "ORBITA_FORM_PUBLIC_RATE_LIMIT_COUNT", 5)
        if count >= max_count:
            return JsonResponse({"ok": False, "error": "Límite de sesiones alcanzado."}, status=429)

        steps = _build_steps(orbita_form)

        session = FormChatSession(
            form=orbita_form,
            session_uuid=_uuid.uuid4(),
            status=FormChatSession.STATUS_STARTED,
            current_step=0,
            total_steps=len(steps),
            ip_address=ip if ip != "unknown" else None,
        )
        session.save()

        logger.info("chat_session started form=%s session=%s", orbita_form.pk, session.session_uuid)

        return JsonResponse({
            "ok": True,
            "session_uuid": str(session.session_uuid),
            "total_steps": len(steps),
            "steps": steps,
        })


class FormChatAnswerAPI(View):
    """POST: guarda la respuesta de un paso y avanza al siguiente."""

    def post(self, request, uuid):
        orbita_form = get_object_or_404(ATSForm, uuid=uuid, is_active=True)

        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"ok": False, "error": "JSON inválido."}, status=400)

        session_uuid = body.get("session_uuid", "")
        step_id = body.get("step_id", "")
        value = body.get("value", "")

        try:
            session = FormChatSession.objects.get(
                session_uuid=session_uuid,
                form=orbita_form,
            )
        except FormChatSession.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Sesión no encontrada."}, status=404)

        if session.status == FormChatSession.STATUS_COMPLETED:
            return JsonResponse({"ok": False, "error": "Sesión ya completada."}, status=400)

        answers = session.answers or {}
        answers[step_id] = value
        session.answers = answers
        session.current_step = min(session.current_step + 1, session.total_steps)
        session.status = FormChatSession.STATUS_IN_PROGRESS

        val_str = str(value).strip()

        if step_id == "submitter_email" or (
            "_email" not in step_id and not session.candidate_email and "@" in val_str
        ):
            session.candidate_email = val_str

        name_keywords = {"nombre", "name", "nombre_completo", "nombre completo", "candidato", "postulante", "solicitante"}
        steps = _build_steps(orbita_form)
        current_step = None
        for s in steps:
            if s["id"] == step_id:
                current_step = s
                break

        if current_step and not session.candidate_name:
            label_lower = current_step["label"].lower()
            if any(kw in label_lower for kw in name_keywords):
                session.candidate_name = val_str[:200]
            elif current_step["type"] in ("text", "textarea") and session.current_step <= 1 and "@" not in val_str and len(val_str) < 80:
                session.candidate_name = val_str[:200]

        is_last = session.current_step >= session.total_steps
        if is_last:
            session.status = FormChatSession.STATUS_COMPLETED
            session.completed_at = timezone.now()

        session.save()

        if is_last:
            self._finalize_submission(request, orbita_form, session)

        return JsonResponse({
            "ok": True,
            "current_step": session.current_step,
            "total_steps": session.total_steps,
            "completed": is_last,
        })

    def _finalize_submission(self, request, orbita_form, session):
        """Al completar el chat, crea la ATSFormSubmission compatible con el sistema existente."""
        answers = session.answers or {}
        pending_files = answers.pop("_pending_files", {})
        steps = _build_steps(orbita_form)

        payload = {}
        submitter_email = session.candidate_email or ""

        for step in steps:
            val = answers.get(step["id"], "")
            if val and step["type"] != "file":
                payload[step["label"]] = val
            elif val and step["type"] == "file":
                payload[step["label"]] = val
            if step["type"] == "email" and val and not submitter_email:
                submitter_email = val

        submission = ATSFormSubmission.objects.create(
            form=orbita_form,
            payload=payload,
            submitter_email=submitter_email,
        )

        session.submission = submission
        session.save(update_fields=["submission"])

        from django.core.files.storage import default_storage
        for step_id, file_info in pending_files.items():
            field_obj = None
            if step_id.startswith("field_"):
                try:
                    field_obj = ATSFormField.objects.get(pk=int(step_id.replace("field_", "")))
                except (ATSFormField.DoesNotExist, ValueError):
                    pass
            try:
                saved_file = default_storage.open(file_info["path"])
                from django.core.files import File
                sub_file = ATSFormSubmissionFile(
                    submission=submission,
                    form_field=field_obj,
                    original_name=file_info["name"],
                )
                sub_file.file.save(file_info["name"], File(saved_file), save=True)
                saved_file.close()
            except Exception as e:
                logger.warning("chat finalize: could not attach file %s: %s", file_info["path"], e)

        if orbita_form.vacancy_id:
            from mi_app.views.orbita.orbita_views import _create_candidate_from_submission
            _create_candidate_from_submission(submission, payload, submitter_email)
            if submission.candidate_id:
                notify_orbita_client(
                    orbita_form.client,
                    ATSNotification.TYPE_CANDIDATE,
                    "Nuevo candidato (chat)",
                    message=f"{submission.candidate.name} — Chat «{orbita_form.name}».",
                    link=reverse("orbita_candidate_detail", args=[submission.candidate.pk]),
                    request=request,
                )
        else:
            notify_orbita_client(
                orbita_form.client,
                ATSNotification.TYPE_SUBMISSION,
                "Nuevo envío (chat)",
                message=f"Chat «{orbita_form.name}»: {submitter_email or 'Sin correo'}.",
                link=reverse("orbita_form_submissions", args=[orbita_form.pk]),
                request=request,
            )

        ip = request.META.get("REMOTE_ADDR", "") or "unknown"
        cache_key = f"orbita_chat_start:{ip}:{orbita_form.uuid}"
        count = cache.get(cache_key, 0)
        timeout = getattr(settings, "ORBITA_FORM_PUBLIC_RATE_LIMIT_SECONDS", 3600)
        cache.set(cache_key, count + 1, timeout=timeout)

        logger.info("chat_session completed form=%s session=%s", orbita_form.pk, session.session_uuid)


class FormChatFileUploadAPI(View):
    """POST: sube un archivo (CV) para un paso tipo file en el chat."""

    def post(self, request, uuid):
        orbita_form = get_object_or_404(ATSForm, uuid=uuid, is_active=True)

        session_uuid = request.POST.get("session_uuid", "")
        step_id = request.POST.get("step_id", "")
        uploaded = request.FILES.get("file")

        try:
            session = FormChatSession.objects.get(session_uuid=session_uuid, form=orbita_form)
        except FormChatSession.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Sesión no encontrada."}, status=404)

        if not uploaded:
            return JsonResponse({"ok": False, "error": "Falta el archivo."}, status=400)

        max_size = getattr(settings, "ORBITA_FORM_PUBLIC_MAX_FILE_SIZE", 10 * 1024 * 1024)
        allowed_ext = getattr(settings, "ORBITA_FORM_PUBLIC_ALLOWED_EXTENSIONS", ["pdf", "doc", "docx"])
        ext = (uploaded.name or "").rsplit(".", 1)[-1].lower() if "." in (uploaded.name or "") else ""
        if uploaded.size > max_size:
            return JsonResponse({"ok": False, "error": f"Archivo supera {max_size // (1024*1024)} MB."}, status=400)
        if ext and allowed_ext and ext not in allowed_ext:
            return JsonResponse({"ok": False, "error": f"Solo se permiten: {', '.join(allowed_ext)}."}, status=400)

        from django.core.files.storage import default_storage
        saved_path = default_storage.save(
            f"orbita/chat_uploads/{session.session_uuid}/{uploaded.name}",
            uploaded,
        )

        answers = session.answers or {}
        answers[step_id] = uploaded.name

        pending_files = answers.get("_pending_files", {})
        pending_files[step_id] = {"path": saved_path, "name": uploaded.name}
        answers["_pending_files"] = pending_files

        session.answers = answers
        session.current_step = min(session.current_step + 1, session.total_steps)
        session.status = FormChatSession.STATUS_IN_PROGRESS

        is_last = session.current_step >= session.total_steps
        if is_last:
            session.status = FormChatSession.STATUS_COMPLETED
            session.completed_at = timezone.now()

        session.save()

        if is_last:
            FormChatAnswerAPI()._finalize_submission(request, orbita_form, session)

        return JsonResponse({
            "ok": True,
            "filename": uploaded.name,
            "current_step": session.current_step,
            "total_steps": session.total_steps,
            "completed": is_last,
        })


class FormChatSessionsView(LoginRequiredMixin, View):
    """Vista del reclutador: historial de sesiones de chat de un formulario."""
    template_name = "orbita/form_chat_sessions.html"
    login_url = "/orbita/plataforma/"

    def get(self, request, pk):
        orbita_form = get_object_or_404(ATSForm, pk=pk)
        orbita_client = getattr(request.user, "ats_client", None)
        if not request.user.is_staff and (not orbita_client or orbita_form.client_id != orbita_client.pk):
            return redirect("orbita_dashboard")

        sessions = orbita_form.chat_sessions.all()[:50]
        steps = _build_steps(orbita_form)

        return render(request, self.template_name, {
            "orbita_form": orbita_form,
            "chat_sessions": sessions,
            "steps": steps,
            "steps_json": json.dumps(steps),
            "orbita_page": "formularios",
            "orbita_client": orbita_client,
        })


class FormChatSessionsListAPI(LoginRequiredMixin, View):
    """GET: devuelve la lista de sesiones como JSON para auto-refresh."""
    login_url = "/orbita/plataforma/"

    def get(self, request, pk):
        orbita_form = get_object_or_404(ATSForm, pk=pk)
        orbita_client = getattr(request.user, "ats_client", None)
        if not request.user.is_staff and (not orbita_client or orbita_form.client_id != orbita_client.pk):
            return JsonResponse({"ok": False}, status=403)

        sessions = orbita_form.chat_sessions.all()[:50]
        items = []
        for s in sessions:
            pct = round((s.current_step / s.total_steps) * 100) if s.total_steps > 0 else 0
            items.append({
                "session_uuid": str(s.session_uuid),
                "status": s.status,
                "status_display": s.get_status_display(),
                "current_step": s.current_step,
                "total_steps": s.total_steps,
                "pct": pct,
                "candidate_name": s.candidate_name or s.candidate_email or "Sin nombre",
                "candidate_email": s.candidate_email or "",
                "source": getattr(s, "source", "web"),
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            })
        return JsonResponse({"ok": True, "sessions": items})


class FormChatSessionDeleteAPI(LoginRequiredMixin, View):
    """POST: elimina una sesión de chat (solo incompletas o cualquiera para el recruiter)."""
    login_url = "/orbita/plataforma/"

    def post(self, request, pk, session_uuid):
        orbita_form = get_object_or_404(ATSForm, pk=pk)
        orbita_client = getattr(request.user, "ats_client", None)
        if not request.user.is_staff and (not orbita_client or orbita_form.client_id != orbita_client.pk):
            return JsonResponse({"ok": False}, status=403)

        try:
            session = FormChatSession.objects.get(session_uuid=session_uuid, form=orbita_form)
        except FormChatSession.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Sesión no encontrada."}, status=404)

        logger.info("chat_session deleted form=%s session=%s by=%s", orbita_form.pk, session.session_uuid, request.user.pk)
        session.delete()
        return JsonResponse({"ok": True})


class FormChatSessionDetailAPI(LoginRequiredMixin, View):
    """GET: polling endpoint para ver el progreso de una sesión en tiempo real."""
    login_url = "/orbita/plataforma/"

    def get(self, request, pk, session_uuid):
        orbita_form = get_object_or_404(ATSForm, pk=pk)
        orbita_client = getattr(request.user, "ats_client", None)
        if not request.user.is_staff and (not orbita_client or orbita_form.client_id != orbita_client.pk):
            return JsonResponse({"ok": False}, status=403)

        try:
            session = FormChatSession.objects.get(session_uuid=session_uuid, form=orbita_form)
        except FormChatSession.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Sesión no encontrada."}, status=404)

        steps = _build_steps(orbita_form)
        conversation = []
        for s in steps:
            val = (session.answers or {}).get(s["id"])
            conversation.append({
                "step_id": s["id"],
                "label": s["label"],
                "type": s["type"],
                "answer": val,
                "answered": val is not None,
            })

        return JsonResponse({
            "ok": True,
            "session_uuid": str(session.session_uuid),
            "status": session.status,
            "current_step": session.current_step,
            "total_steps": session.total_steps,
            "candidate_name": session.candidate_name or session.candidate_email or "Sin nombre",
            "candidate_email": session.candidate_email,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "conversation": conversation,
        })


class CandidateChatSessionAPI(LoginRequiredMixin, View):
    """GET: polling endpoint para ver progreso del chat desde el detalle del candidato."""
    login_url = "/orbita/plataforma/"

    def get(self, request, session_uuid):
        from mi_app.models import Candidate
        orbita_client = getattr(request.user, "ats_client", None)
        if not request.user.is_staff and not orbita_client:
            return JsonResponse({"ok": False}, status=403)

        try:
            session = FormChatSession.objects.select_related("form").get(session_uuid=session_uuid)
        except FormChatSession.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Sesión no encontrada."}, status=404)

        if not request.user.is_staff and session.form.client_id != orbita_client.pk:
            return JsonResponse({"ok": False}, status=403)

        steps = _build_steps(session.form)
        conversation = []
        for i, s in enumerate(steps):
            val = (session.answers or {}).get(s["id"])
            conversation.append({
                "step_id": s["id"],
                "label": s["label"],
                "type": s["type"],
                "answer": val,
                "answered": val is not None,
                "is_current": i == session.current_step and session.status != "completed",
            })

        return JsonResponse({
            "ok": True,
            "status": session.status,
            "status_display": session.get_status_display(),
            "current_step": session.current_step,
            "total_steps": session.total_steps,
            "candidate_name": session.candidate_name or session.candidate_email or "Sin nombre",
            "candidate_email": session.candidate_email,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "conversation": conversation,
        })










