"""
Bot de Telegram para Órbita — postulación conversacional.

Flujo:
  /start <form_uuid>  → muestra la vacante y pregunta si quiere postularse
  "Sí, iniciar"       → crea FormChatSession, pregunta campo por campo
  Cada respuesta       → guarda en session.answers, avanza paso
  Al terminar          → crea ATSFormSubmission + Candidate (si aplica)
"""
import logging
import uuid as _uuid

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import close_old_connections
from django.db.utils import InterfaceError, OperationalError
from django.urls import reverse
from django.utils import timezone

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logger = logging.getLogger(__name__)

CHOOSING, ANSWERING = range(2)


def _telegram_display_name(user):
    if not user:
        return ""
    first_name = (getattr(user, "first_name", "") or "").strip()
    last_name = (getattr(user, "last_name", "") or "").strip()
    display_name = " ".join([part for part in (first_name, last_name) if part]).strip()
    if display_name:
        return display_name[:200]
    username = (getattr(user, "username", "") or "").strip()
    if username:
        return f"@{username}"[:200]
    return ""


def _candidate_name_is_generic(name, email=""):
    clean = (str(name or "").strip()).lower()
    if not clean:
        return True
    if clean in {"postulante", "candidato", "candidate", "applicant"}:
        return True
    if email:
        local_part = (email.split("@")[0] if "@" in email else "").strip().lower()
        if local_part and clean == local_part:
            return True
    return False


def _thanks_name(session):
    direct_name = (session.candidate_name or "").strip()
    if direct_name and not _candidate_name_is_generic(direct_name, session.candidate_email or ""):
        return direct_name
    answers = session.answers or {}
    tg_meta = answers.get("_telegram", {}) if isinstance(answers, dict) else {}
    tg_name = (tg_meta.get("display_name") or "").strip() if isinstance(tg_meta, dict) else ""
    if tg_name:
        return tg_name
    if direct_name:
        return direct_name
    return ""


def _get_form(uuid_str):
    from mi_app.models import ATSForm
    close_old_connections()
    try:
        return ATSForm.objects.select_related("vacancy", "client").get(
            uuid=uuid_str, is_active=True
        )
    except (InterfaceError, OperationalError):
        logger.warning("telegram_bot: DB connection stale while loading form, retrying once")
        close_old_connections()
        try:
            return ATSForm.objects.select_related("vacancy", "client").get(
                uuid=uuid_str, is_active=True
            )
        except (ATSForm.DoesNotExist, ValueError):
            return None
        except (InterfaceError, OperationalError):
            logger.exception("telegram_bot: DB unavailable while loading form")
            return None
    except (ATSForm.DoesNotExist, ValueError):
        return None


def _build_steps(orbita_form):
    from mi_app.views.orbita.form_chat_views import _build_steps as _bs
    return _bs(orbita_form)


def _create_session(orbita_form, steps, telegram_user_id, telegram_display_name="", telegram_username=""):
    from mi_app.models import FormChatSession
    close_old_connections()
    answers = {
        "_telegram": {
            "id": telegram_user_id,
            "username": telegram_username or "",
            "display_name": telegram_display_name or "",
        }
    }
    session = FormChatSession(
        form=orbita_form,
        session_uuid=_uuid.uuid4(),
        status=FormChatSession.STATUS_STARTED,
        current_step=0,
        total_steps=len(steps),
        answers=answers,
        candidate_name=(telegram_display_name or "")[:200],
        telegram_user_id=telegram_user_id,
        source=FormChatSession.SOURCE_TELEGRAM,
        ip_address=None,
    )
    session.save()
    return session


def _get_session(session_id):
    from mi_app.models import FormChatSession
    close_old_connections()
    try:
        return FormChatSession.objects.get(pk=session_id)
    except (InterfaceError, OperationalError):
        logger.warning("telegram_bot: DB connection stale while loading session, retrying once")
        close_old_connections()
        try:
            return FormChatSession.objects.get(pk=session_id)
        except (FormChatSession.DoesNotExist, InterfaceError, OperationalError):
            logger.exception("telegram_bot: failed to load chat session")
            return None
    except FormChatSession.DoesNotExist:
        return None


def _save_answer(session, step, value, orbita_form):
    from mi_app.models import FormChatSession

    close_old_connections()
    answers = session.answers or {}
    answers[step["id"]] = value
    session.answers = answers
    session.current_step = min(session.current_step + 1, session.total_steps)
    session.status = FormChatSession.STATUS_IN_PROGRESS

    val_str = str(value).strip()
    if step["id"] == "submitter_email" or (
        step["type"] == "email" and val_str and "@" in val_str
    ):
        session.candidate_email = val_str

    name_keywords = {
        "nombre",
        "name",
        "nombre completo",
        "full name",
        "nombre y apellidos",
        "apellidos",
    }
    label_lower = (step.get("label") or "").lower()
    if (
        val_str
        and step["type"] in ("text", "textarea")
        and any(kw in label_lower for kw in name_keywords)
        and "@" not in val_str
    ):
        session.candidate_name = val_str[:200]

    is_last = session.current_step >= session.total_steps
    if is_last:
        session.status = FormChatSession.STATUS_COMPLETED
        session.completed_at = timezone.now()

    session.save()
    return is_last


def _finalize(orbita_form, session):
    """Replica la lógica de FormChatAnswerAPI._finalize_submission sin request."""
    from mi_app.models import (
        ATSFormSubmission, ATSFormSubmissionFile, ATSFormField,
        ATSNotification, FormChatSession,
    )
    from mi_app.orbita_notifications import notify_orbita_client

    close_old_connections()
    session = FormChatSession.objects.get(pk=session.pk)
    answers = session.answers or {}
    pending_files = answers.pop("_pending_files", {})
    logger.info("telegram_bot _finalize: pending_files=%s", list(pending_files.keys()))
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
    from django.core.files import File
    for step_id, file_info in pending_files.items():
        field_obj = None
        if step_id.startswith("field_"):
            try:
                field_obj = ATSFormField.objects.get(pk=int(step_id.replace("field_", "")))
            except (ATSFormField.DoesNotExist, ValueError):
                pass
        try:
            saved_file = default_storage.open(file_info["path"])
            sub_file = ATSFormSubmissionFile(
                submission=submission,
                form_field=field_obj,
                original_name=file_info["name"],
            )
            sub_file.file.save(file_info["name"], File(saved_file), save=True)
            saved_file.close()
            logger.info("telegram_bot: attached file %s to submission %s", file_info["name"], submission.pk)
        except Exception as e:
            logger.warning("telegram_bot: could not attach file %s: %s", file_info.get("path"), e)

    if orbita_form.vacancy_id:
        from mi_app.views.orbita.orbita_views import _create_candidate_from_submission
        _create_candidate_from_submission(submission, payload, submitter_email)
        if submission.candidate_id:
            tg_meta = (session.answers or {}).get("_telegram", {})
            tg_name = (tg_meta.get("display_name") or "").strip() if isinstance(tg_meta, dict) else ""
            if tg_name and _candidate_name_is_generic(submission.candidate.name, submitter_email):
                submission.candidate.name = tg_name[:255]
                submission.candidate.save(update_fields=["name"])
            notify_orbita_client(
                orbita_form.client,
                ATSNotification.TYPE_CANDIDATE,
                "Nuevo candidato (Telegram)",
                message=f"{submission.candidate.name} — Telegram «{orbita_form.name}».",
                link=reverse("orbita_candidate_detail", args=[submission.candidate.pk]),
            )
    else:
        notify_orbita_client(
            orbita_form.client,
            ATSNotification.TYPE_SUBMISSION,
            "Nuevo envío (Telegram)",
            message=f"Telegram «{orbita_form.name}»: {submitter_email or 'Sin correo'}.",
            link=reverse("orbita_form_submissions", args=[orbita_form.pk]),
        )
    logger.info("telegram_bot: session completed form=%s session=%s", orbita_form.pk, session.session_uuid)


# ──────────────────────────── Handlers ────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Hola, soy Orbita.\n\n"
            "Para iniciar una postulación necesito que abras el enlace que te compartieron.\n"
            "Formato: /start <codigo_del_formulario>",
        )
        return ConversationHandler.END

    form_uuid = args[0]
    orbita_form = await sync_to_async(_get_form)(form_uuid)
    if not orbita_form:
        await update.message.reply_text(
            "❌ No encontré esa vacante o el formulario no está activo.\n"
            "Verifica el enlace e intenta de nuevo.",
        )
        return ConversationHandler.END

    context.user_data["form_uuid"] = form_uuid
    context.user_data["orbita_form_id"] = orbita_form.pk

    vacancy = orbita_form.vacancy
    if vacancy:
        text = (
            f"🏢 *{vacancy.title}*\n\n"
            f"{vacancy.description[:1500] if vacancy.description else 'Sin descripción disponible.'}\n\n"
            "─────────────────────\n"
            "¿Te interesa esta vacante? Presiona el botón para iniciar tu postulación."
        )
    else:
        text = (
            f"📋 *{orbita_form.name}*\n\n"
            f"{orbita_form.description[:1000] if orbita_form.description else ''}\n\n"
            "¿Listo para completar tu postulación? Presiona el botón para comenzar."
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Iniciar postulación", callback_data="apply_yes")],
        [InlineKeyboardButton("Ahora no", callback_data="apply_no")],
    ])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
    return CHOOSING


async def apply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "apply_no":
        await query.edit_message_text(
            "Sin problema. Si cambias de opinion, vuelve a abrir el enlace cuando quieras."
        )
        return ConversationHandler.END

    form_uuid = context.user_data.get("form_uuid")
    orbita_form = await sync_to_async(_get_form)(form_uuid)
    if not orbita_form:
        await query.edit_message_text("❌ Formulario no disponible.")
        return ConversationHandler.END

    steps = await sync_to_async(_build_steps)(orbita_form)
    if not steps:
        await query.edit_message_text("⚠️ Este formulario no tiene campos configurados.")
        return ConversationHandler.END

    tg_user = update.effective_user
    tg_display_name = _telegram_display_name(tg_user)
    tg_username = (getattr(tg_user, "username", "") or "").strip()
    session = await sync_to_async(_create_session)(
        orbita_form,
        steps,
        update.effective_user.id,
        tg_display_name,
        tg_username,
    )

    context.user_data["session_id"] = session.pk
    context.user_data["steps"] = steps
    context.user_data["current_step"] = 0

    step = steps[0]
    total = len(steps)
    msg = _format_question(step, 1, total)

    await query.edit_message_text(
        "Perfecto, iniciamos tu postulación.\n\n"
        "Te voy a hacer algunas preguntas, una por una.\n"
        "Si un campo es de archivo y no lo tienes, escribe `omitir`.\n\n"
        "─────────────────────\n\n" + msg,
        parse_mode="Markdown",
    )
    return ANSWERING


def _format_question(step, num, total):
    emoji_map = {
        "text": "📝",
        "email": "📧",
        "phone": "📱",
        "textarea": "📄",
        "radio": "🔘",
        "multi_select": "☑️",
        "file": "📎",
    }
    emoji = emoji_map.get(step["type"], "📝")
    required = " *(obligatorio)*" if step.get("required") else " _(opcional)_"
    hint = ""
    if step["placeholder"]:
        hint = f"\n💡 _Ej: {step['placeholder']}_"
    if step["type"] == "file":
        hint = "\n💡 _Envía un archivo PDF/DOC o escribe_ `omitir`"
    options = step.get("options") or []
    if options:
        hint += "\nOpciones:\n" + "\n".join([f"• {o}" for o in options[:12]])

    return (
        f"{emoji} *Pregunta {num}/{total}*\n"
        f"{step['label']}{required}{hint}"
    )


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    steps = context.user_data.get("steps", [])
    idx = context.user_data.get("current_step", 0)
    session_id = context.user_data.get("session_id")
    form_uuid = context.user_data.get("form_uuid")

    if idx >= len(steps) or not session_id:
        await update.message.reply_text("⚠️ No hay una sesión activa. Usa /start para comenzar.")
        return ConversationHandler.END

    step = steps[idx]
    value = (update.message.text or "").strip()

    if step["type"] == "file":
        if value.lower() in ("omitir", "skip", "no", "no tengo"):
            value = ""
        else:
            await update.message.reply_text(
                "📎 Por favor, envía el archivo directamente (arrástralo o usa el clip 📎).\n"
                "Si no tienes el archivo, escribe `omitir`."
            )
            return ANSWERING

    if step["type"] == "email" and value and "@" not in value:
        await update.message.reply_text("⚠️ Introduce un correo electrónico válido.")
        return ANSWERING

    if step.get("required") and not value:
        await update.message.reply_text("⚠️ Este campo es obligatorio. Por favor, responde.")
        return ANSWERING

    session = await sync_to_async(_get_session)(session_id)
    if not session:
        await update.message.reply_text(
            "⚠️ Tuvimos un problema temporal de conexión. Intenta de nuevo en unos segundos."
        )
        return ConversationHandler.END

    orbita_form = await sync_to_async(_get_form)(form_uuid)
    is_last = await sync_to_async(_save_answer)(session, step, value, orbita_form)

    if is_last:
        await sync_to_async(_finalize)(orbita_form, session)
        session = await sync_to_async(_get_session)(session_id)
        if not session:
            await update.message.reply_text(
                "Tu postulación se envió, pero no pude refrescar el estado. Si quieres, vuelve a abrir el enlace."
            )
            return ConversationHandler.END
        name = _thanks_name(session)
        intro = f"Gracias, {name}. " if name else "Gracias. "
        await update.message.reply_text(
            "Postulación completada.\n\n"
            f"{intro}Tu información ya fue enviada al equipo de reclutamiento.\n\n"
            "Si tu perfil avanza, te van a contactar por este medio o por correo."
        )
        return ConversationHandler.END

    next_idx = idx + 1
    context.user_data["current_step"] = next_idx

    pct = round((next_idx / len(steps)) * 100)
    bar_filled = round(pct / 10)
    bar = "▓" * bar_filled + "░" * (10 - bar_filled)

    next_step = steps[next_idx]
    msg = (
        f"✅ Respuesta guardada.\n"
        f"Progreso: `[{bar}]` {pct}%\n\n"
        + _format_question(next_step, next_idx + 1, len(steps))
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ANSWERING


async def _download_and_store_file(update, context, session, step_id):
    """Descarga el archivo de Telegram y lo guarda en default_storage."""
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    from mi_app.models import FormChatSession

    doc = update.message.document
    if not doc:
        return None, None

    file_name = doc.file_name or "archivo"
    logger.info("telegram_bot: downloading file %s (size=%s)", file_name, doc.file_size)

    tg_file = await context.bot.get_file(doc.file_id)
    file_bytes = await tg_file.download_as_bytearray()
    logger.info("telegram_bot: downloaded %d bytes", len(file_bytes))

    save_dir = f"orbita/chat_uploads/{session.session_uuid}"
    saved_path = await sync_to_async(default_storage.save)(
        f"{save_dir}/{file_name}",
        ContentFile(bytes(file_bytes)),
    )
    logger.info("telegram_bot: file saved to %s", saved_path)

    session = await sync_to_async(
        lambda: FormChatSession.objects.get(pk=session.pk)
    )()
    answers = session.answers or {}
    pending_files = answers.get("_pending_files", {})
    pending_files[step_id] = {"path": saved_path, "name": file_name}
    answers["_pending_files"] = pending_files
    answers[step_id] = file_name
    session.answers = answers
    await sync_to_async(session.save)(update_fields=["answers"])
    logger.info("telegram_bot: pending_files keys=%s", list(answers.get("_pending_files", {}).keys()))

    return file_name, saved_path


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file uploads for file-type steps."""
    steps = context.user_data.get("steps", [])
    idx = context.user_data.get("current_step", 0)
    session_id = context.user_data.get("session_id")
    form_uuid = context.user_data.get("form_uuid")

    if idx >= len(steps) or not session_id:
        await update.message.reply_text("⚠️ No hay una sesión activa.")
        return ConversationHandler.END

    step = steps[idx]
    if step["type"] != "file":
        await update.message.reply_text(
            "📝 En este paso necesito una respuesta de texto, no un archivo.\n"
            "Por favor, escribe tu respuesta."
        )
        return ANSWERING

    session = await sync_to_async(_get_session)(session_id)
    if not session:
        await update.message.reply_text(
            "⚠️ Tuvimos un problema temporal de conexión. Intenta de nuevo en unos segundos."
        )
        return ConversationHandler.END
    orbita_form = await sync_to_async(_get_form)(form_uuid)

    file_name, saved_path = await _download_and_store_file(
        update, context, session, step["id"]
    )
    if not file_name:
        await update.message.reply_text("⚠️ No pude recibir el archivo. Intenta de nuevo.")
        return ANSWERING

    session = await sync_to_async(_get_session)(session_id)
    if not session:
        await update.message.reply_text(
            "Tu archivo se recibió, pero no pude continuar por un problema temporal. Intenta nuevamente."
        )
        return ConversationHandler.END
    session.current_step = min(session.current_step + 1, session.total_steps)
    session.status = FormChatSession.STATUS_IN_PROGRESS

    is_last = session.current_step >= session.total_steps
    if is_last:
        session.status = FormChatSession.STATUS_COMPLETED
        session.completed_at = timezone.now()
    await sync_to_async(session.save)()

    if is_last:
        await sync_to_async(_finalize)(orbita_form, session)
        session = await sync_to_async(_get_session)(session_id)
        if not session:
            await update.message.reply_text(
                "Tu postulación se envió, pero no pude refrescar el estado. Si quieres, vuelve a abrir el enlace."
            )
            return ConversationHandler.END
        name = _thanks_name(session)
        intro = f"Gracias, {name}. " if name else "Gracias. "
        await update.message.reply_text(
            "Postulación completada.\n\n"
            f"{intro}Tu información ya fue enviada al equipo de reclutamiento.\n\n"
            "Si tu perfil avanza, te van a contactar por este medio o por correo."
        )
        return ConversationHandler.END

    next_idx = idx + 1
    context.user_data["current_step"] = next_idx

    pct = round((next_idx / len(steps)) * 100)
    bar_filled = round(pct / 10)
    bar = "▓" * bar_filled + "░" * (10 - bar_filled)

    next_step = steps[next_idx]
    msg = (
        f"✅ Archivo recibido: _{file_name}_\n"
        f"Progreso: `[{bar}]` {pct}%\n\n"
        + _format_question(next_step, next_idx + 1, len(steps))
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ANSWERING


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Postulación cancelada.\n"
        "Si quieres retomarla, vuelve a abrir el enlace del formulario."
    )
    return ConversationHandler.END


def build_application():
    """Construye la aplicación de Telegram con todos los handlers."""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN no configurado en settings/env.")

    app = Application.builder().token(token).build()

    async def _on_error(update, context):
        logger.exception("telegram_bot: unhandled error", exc_info=context.error)

    app.add_error_handler(_on_error)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            CHOOSING: [CallbackQueryHandler(apply_callback)],
            ANSWERING: [
                MessageHandler(filters.Document.ALL, handle_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer),
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv_handler)
    return app





