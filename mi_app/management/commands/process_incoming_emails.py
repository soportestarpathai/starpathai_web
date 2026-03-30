"""
Procesa correos entrantes por IMAP y los convierte en postulaciones ATS.

Prioridad de conexión:
1) IMAP configurado por cliente en Config. correo.
2) Buzón global por ENV (fallback para clientes sin IMAP propio).

Uso:
  python manage.py process_incoming_emails --once
  python manage.py process_incoming_emails --loop --interval 60
  python manage.py process_incoming_emails --once --dry-run
"""
from __future__ import annotations

import imaplib
import logging
import os
import re
import time
from dataclasses import dataclass
from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import getaddresses, parseaddr
from typing import Dict, List, Optional, Sequence, Set, Tuple

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.urls import reverse

from mi_app.ats_notifications import notify_ats_client
from mi_app.models import ATSClientEmailConfig, ATSForm, ATSFormSubmission, ATSFormSubmissionFile, ATSNotification
from mi_app.views.ats.ats_views import _create_candidate_from_submission

logger = logging.getLogger(__name__)


@dataclass
class ParsedAttachment:
    name: str
    content: bytes


@dataclass(frozen=True)
class MailboxConnection:
    host: str
    port: int
    user: str
    password: str
    folder: str
    use_ssl: bool
    source: str


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _decode_mime(value: str) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _extract_emails_from_header_values(values: Sequence[str]) -> Set[str]:
    pairs = getaddresses([v for v in values if v])
    emails = set()
    for _name, addr in pairs:
        addr = (addr or "").strip().lower()
        if addr and "@" in addr:
            emails.add(addr)
    return emails


def _extract_plain_text(msg) -> str:
    chunks: List[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            disposition = (part.get_content_disposition() or "").lower()
            if disposition == "attachment":
                continue
            content_type = (part.get_content_type() or "").lower()
            if content_type != "text/plain":
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                chunks.append(payload.decode(charset, errors="replace"))
            except Exception:
                chunks.append(payload.decode("utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                chunks.append(payload.decode(charset, errors="replace"))
            except Exception:
                chunks.append(payload.decode("utf-8", errors="replace"))
    return "\n".join(chunks).strip()


def _extract_attachments(msg, allowed_ext: Set[str]) -> List[ParsedAttachment]:
    found: List[ParsedAttachment] = []
    for part in msg.walk():
        content_disposition = (part.get_content_disposition() or "").lower()
        filename = _decode_mime(part.get_filename() or "").strip()
        if content_disposition != "attachment" and not filename:
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        safe_name = filename or "adjunto.bin"
        ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
        if allowed_ext and ext and ext not in allowed_ext:
            continue
        found.append(ParsedAttachment(name=safe_name, content=payload))
    return found


def _candidate_inbox_addresses(config: ATSClientEmailConfig) -> Set[str]:
    values = [
        (config.company_from_email or "").strip().lower(),
        (config.notification_email or "").strip().lower(),
        (config.smtp_user or "").strip().lower(),
        (getattr(config, "imap_user", "") or "").strip().lower(),
    ]
    return {v for v in values if v and "@" in v}


def _match_config_for_email(
    subject: str,
    recipient_emails: Set[str],
    configs: Sequence[ATSClientEmailConfig],
) -> Optional[ATSClientEmailConfig]:
    candidates: List[Tuple[int, ATSClientEmailConfig]] = []
    for config in configs:
        pattern = (config.incoming_subject_regex or "").strip()
        if not pattern:
            continue
        try:
            if not re.search(pattern, subject or ""):
                continue
        except re.error:
            logger.warning("Regex inválida en config %s: %s", config.pk, pattern)
            continue
        score = 1
        inbox_addresses = _candidate_inbox_addresses(config)
        if inbox_addresses and recipient_emails.intersection(inbox_addresses):
            score = 2
        candidates.append((score, config))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1].pk), reverse=True)
    return candidates[0][1]


def _pick_target_form(client, subject: str, body: str) -> Optional[ATSForm]:
    forms = list(
        ATSForm.objects.filter(client=client, is_active=True)
        .select_related("vacancy")
        .order_by("-updated_at", "-id")
    )
    if not forms:
        return None

    lookup_text = f"{subject}\n{body}".lower()
    for form in forms:
        vacancy_title = (getattr(form.vacancy, "title", "") or "").strip().lower()
        if vacancy_title and vacancy_title in lookup_text:
            return form

    for form in forms:
        if form.vacancy_id:
            return form
    return forms[0]


def _candidate_name_from_sender(from_name: str, from_email: str) -> str:
    clean_name = (from_name or "").strip()
    if clean_name:
        return clean_name[:255]
    if from_email and "@" in from_email:
        return from_email.split("@", 1)[0][:255]
    return "Postulante"


class Command(BaseCommand):
    help = "Lee correos entrantes por IMAP y crea postulaciones ATS según regex de asunto."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Ejecuta una sola lectura y termina.")
        parser.add_argument("--loop", action="store_true", help="Ejecuta en bucle continuo.")
        parser.add_argument("--interval", type=int, default=60, help="Segundos entre ciclos cuando se usa --loop.")
        parser.add_argument("--max-emails", type=int, default=20, help="Máximo de correos UNSEEN por ciclo.")
        parser.add_argument("--dry-run", action="store_true", help="No guarda en BD ni marca correos como leídos.")

    def handle(self, *args, **options):
        run_once = bool(options.get("once"))
        run_loop = bool(options.get("loop"))
        interval = max(int(options.get("interval") or 60), 10)
        max_emails = max(int(options.get("max_emails") or 20), 1)
        dry_run = bool(options.get("dry_run"))

        if not run_once and not run_loop:
            run_once = True

        allowed_ext = {
            e.strip().lower()
            for e in getattr(settings, "ATS_FORM_PUBLIC_ALLOWED_EXTENSIONS", ["pdf", "doc", "docx"])
            if e and str(e).strip()
        }
        self.stdout.write(self.style.SUCCESS("Procesador de correo entrante ATS iniciado."))
        if dry_run:
            self.stdout.write(self.style.WARNING("Modo dry-run activo: no se guardarán cambios."))

        while True:
            try:
                self._run_cycle(max_emails=max_emails, dry_run=dry_run, allowed_ext=allowed_ext)
            except Exception as exc:
                logger.exception("Error en ciclo de correo entrante: %s", exc)
                self.stdout.write(self.style.ERROR(f"Error en ciclo: {exc}"))

            if run_once:
                break
            time.sleep(interval)

    def _run_cycle(self, max_emails: int, dry_run: bool, allowed_ext: Set[str]) -> None:
        configs = list(
            ATSClientEmailConfig.objects.select_related("client", "client__user")
            .exclude(incoming_subject_regex="")
            .order_by("id")
        )
        if not configs:
            self.stdout.write("No hay clientes con regex de asunto configurada.")
            return

        mailboxes = self._resolve_mailboxes(configs)
        if not mailboxes:
            self.stdout.write(
                self.style.WARNING(
                    "No hay buzones IMAP configurados. Configura IMAP por cliente en Config. correo "
                    "o define ATS_IMAP_* como fallback global."
                )
            )
            return

        for mailbox_conn, mailbox_configs in mailboxes.items():
            self._process_mailbox(
                mailbox_conn=mailbox_conn,
                configs=mailbox_configs,
                max_emails=max_emails,
                dry_run=dry_run,
                allowed_ext=allowed_ext,
            )

    def _resolve_mailboxes(
        self,
        configs: Sequence[ATSClientEmailConfig],
    ) -> Dict[MailboxConnection, List[ATSClientEmailConfig]]:
        groups: Dict[MailboxConnection, List[ATSClientEmailConfig]] = {}
        client_ids_with_imap: Set[int] = set()

        for config in configs:
            if not getattr(config, "imap_enabled", False):
                continue
            host = (getattr(config, "imap_host", "") or "").strip()
            user = (getattr(config, "imap_user", "") or "").strip()
            password = (getattr(config, "imap_password_encrypted", "") or "").strip()
            folder = (getattr(config, "imap_folder", "") or "").strip() or "INBOX"
            port = int(getattr(config, "imap_port", 993) or 993)
            use_ssl = bool(getattr(config, "imap_use_ssl", True))

            if not host or not user or not password:
                logger.warning(
                    "IMAP habilitado pero incompleto en config=%s client=%s",
                    config.pk,
                    config.client_id,
                )
                continue

            conn = MailboxConnection(
                host=host,
                port=port,
                user=user,
                password=password,
                folder=folder,
                use_ssl=use_ssl,
                source="client",
            )
            groups.setdefault(conn, []).append(config)
            client_ids_with_imap.add(config.client_id)

        fallback_host = (os.environ.get("ATS_IMAP_HOST") or "").strip()
        fallback_user = (os.environ.get("ATS_IMAP_USER") or "").strip()
        fallback_password = (os.environ.get("ATS_IMAP_PASSWORD") or "").strip()
        if fallback_host and fallback_user and fallback_password:
            fallback_conn = MailboxConnection(
                host=fallback_host,
                port=int((os.environ.get("ATS_IMAP_PORT") or "993").strip() or "993"),
                user=fallback_user,
                password=fallback_password,
                folder=(os.environ.get("ATS_IMAP_FOLDER") or "INBOX").strip() or "INBOX",
                use_ssl=_env_bool("ATS_IMAP_USE_SSL", True),
                source="env",
            )
            fallback_configs = [c for c in configs if c.client_id not in client_ids_with_imap]
            if fallback_configs:
                groups.setdefault(fallback_conn, []).extend(fallback_configs)

        return groups

    def _process_mailbox(
        self,
        mailbox_conn: MailboxConnection,
        configs: Sequence[ATSClientEmailConfig],
        max_emails: int,
        dry_run: bool,
        allowed_ext: Set[str],
    ) -> None:
        if not configs:
            return
        mailbox_cls = imaplib.IMAP4_SSL if mailbox_conn.use_ssl else imaplib.IMAP4
        mailbox = mailbox_cls(mailbox_conn.host, mailbox_conn.port)
        try:
            mailbox.login(mailbox_conn.user, mailbox_conn.password)
            mailbox.select(mailbox_conn.folder)

            status, ids_data = mailbox.search(None, "UNSEEN")
            if status != "OK":
                self.stdout.write(
                    self.style.WARNING(
                        f"No se pudo consultar UNSEEN en {mailbox_conn.user}@{mailbox_conn.host}."
                    )
                )
                return

            raw_ids = ids_data[0].split() if ids_data and ids_data[0] else []
            if not raw_ids:
                self.stdout.write(f"Sin correos nuevos en {mailbox_conn.user}.")
                return

            ids = raw_ids[-max_emails:]
            self.stdout.write(
                f"Mailbox {mailbox_conn.user} ({mailbox_conn.source}) UNSEEN={len(raw_ids)} | procesando={len(ids)}"
            )

            for msg_id in ids:
                status, msg_data = mailbox.fetch(msg_id, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue
                raw_email = msg_data[0][1]
                msg = message_from_bytes(raw_email)

                subject = _decode_mime(msg.get("Subject", "")).strip()
                from_name, from_email = parseaddr(_decode_mime(msg.get("From", "")))
                from_name = (from_name or "").strip()
                from_email = (from_email or "").strip().lower()
                recipients = _extract_emails_from_header_values(
                    [
                        msg.get("To", ""),
                        msg.get("Cc", ""),
                        msg.get("Delivered-To", ""),
                        msg.get("X-Original-To", ""),
                    ]
                )
                body = _extract_plain_text(msg)
                attachments = _extract_attachments(msg, allowed_ext=allowed_ext)

                config = _match_config_for_email(subject, recipients, configs)
                if not config:
                    self.stdout.write(
                        f"SKIP #{msg_id.decode()} mailbox={mailbox_conn.user} sin match de regex: {subject[:90]}"
                    )
                    if not dry_run:
                        mailbox.store(msg_id, "+FLAGS", "\\Seen")
                    continue

                target_form = _pick_target_form(config.client, subject=subject, body=body)
                if not target_form:
                    self.stdout.write(
                        self.style.WARNING(
                            f"SKIP #{msg_id.decode()} cliente={config.client.company_name} sin formulario activo."
                        )
                    )
                    if not dry_run:
                        mailbox.store(msg_id, "+FLAGS", "\\Seen")
                    continue

                payload = {
                    "Canal": "Correo entrante",
                    "Asunto": subject,
                    "Remitente": from_email or from_name or "desconocido",
                    "Destinatarios": ", ".join(sorted(recipients)),
                    "Mensaje": (body or "")[:10000],
                }

                self.stdout.write(
                    f"MATCH #{msg_id.decode()} cliente={config.client.company_name} form={target_form.name} asunto={subject[:70]}"
                )
                if dry_run:
                    continue

                submission = ATSFormSubmission.objects.create(
                    form=target_form,
                    payload=payload,
                    submitter_email=from_email,
                )

                for attachment in attachments:
                    sub_file = ATSFormSubmissionFile(
                        submission=submission,
                        form_field=None,
                        original_name=attachment.name,
                    )
                    sub_file.file.save(attachment.name, ContentFile(attachment.content), save=True)

                candidate = None
                if target_form.vacancy_id:
                    candidate = _create_candidate_from_submission(submission, payload, from_email)
                    if candidate:
                        current_name = (candidate.name or "").strip()
                        local_part = from_email.split("@", 1)[0] if "@" in from_email else ""
                        if from_name and current_name.lower() in {"postulante", local_part.lower()}:
                            candidate.name = _candidate_name_from_sender(from_name, from_email)
                            candidate.save(update_fields=["name"])

                if candidate:
                    notify_ats_client(
                        config.client,
                        ATSNotification.TYPE_CANDIDATE,
                        "Nuevo candidato (correo entrante)",
                        message=f"{candidate.name} — Correo «{subject[:120]}».",
                        link=reverse("ats_candidate_detail", args=[candidate.pk]),
                    )
                else:
                    notify_ats_client(
                        config.client,
                        ATSNotification.TYPE_SUBMISSION,
                        "Nuevo envío (correo entrante)",
                        message=f"Correo «{subject[:120]}».",
                        link=reverse("ats_form_submissions", args=[target_form.pk]),
                    )

                mailbox.store(msg_id, "+FLAGS", "\\Seen")

        finally:
            try:
                mailbox.close()
            except Exception:
                pass
            try:
                mailbox.logout()
            except Exception:
                pass
