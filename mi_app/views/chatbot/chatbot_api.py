from __future__ import annotations

import logging
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle

from mi_app.views.chatbot.services.kb_xml import search_kb

logger = logging.getLogger(__name__)


class ChatAPIView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "chat"

    MAX_MSG_LEN = 2000
    MAX_HISTORY_MSGS = 12  # 6 turnos (user+bot)

    GREETING_PATTERNS = [
        r"\bhola\b",
        r"\bbuen(as|os)?\b",
        r"\bhey\b",
        r"\bhello\b",
        r"\bme puedes ayudar\b",
        r"\bpuedes ayudarme\b",
        r"\bnecesito ayuda\b",
        r"\bayuda\b",
    ]

    @classmethod
    def is_greeting(cls, text: str) -> bool:
        t = (text or "").lower().strip()
        for p in cls.GREETING_PATTERNS:
            if re.search(p, t):
                return True
        return False

    def post(self, request, *args, **kwargs):
        session_id = request.data.get("session_id")
        message = (request.data.get("message") or "").strip()
        history = request.data.get("history") or []
        reset = bool(request.data.get("reset", False))

        _sid = (session_id or "")[:12] + ("…" if (session_id and len(session_id) > 12) else "")
        logger.info(
            "chat_post inicio session_id=%s reset=%s message_len=%s",
            _sid or "(vacío)",
            reset,
            len(message),
        )

        if not session_id:
            logger.warning("chat_post falta session_id")
            return Response({"detail": "Falta session_id"}, status=status.HTTP_400_BAD_REQUEST)

        if reset:
            logger.info("chat_post reset conversación session_id=%s", _sid or session_id)
            return Response(
                {"session_id": session_id, "reply": "🧹 Listo, reinicié la conversación.", "sources": []},
                status=status.HTTP_200_OK,
            )

        if not message:
            logger.warning("chat_post mensaje vacío")
            return Response({"detail": "Mensaje vacío"}, status=status.HTTP_400_BAD_REQUEST)

        if len(message) > self.MAX_MSG_LEN:
            logger.warning("chat_post mensaje demasiado largo len=%s", len(message))
            return Response({"detail": "Mensaje demasiado largo."}, status=status.HTTP_400_BAD_REQUEST)

        if self.is_greeting(message):
            logger.info("chat_post respuesta saludo (sin KB)")
            return Response(
                {
                    "session_id": session_id,
                    "reply": "Hola 👋 Soy el asistente de StarPath. ¿En qué puedo ayudarte?",
                    "sources": [],
                },
                status=status.HTTP_200_OK,
            )

        safe_history = []
        if isinstance(history, list):
            for m in history[-self.MAX_HISTORY_MSGS :]:
                if not isinstance(m, dict):
                    continue
                role = m.get("role")
                content = (m.get("content") or "").strip()
                if role not in ("user", "bot"):
                    continue
                if not content:
                    continue
                safe_history.append({"role": role, "content": content[: self.MAX_MSG_LEN]})

        logger.debug("chat_post buscando en KB query=%s history_len=%s", message[:80], len(safe_history))
        hits = search_kb(message, limit=3)

        sources = [{"id": h.id, "title": h.title or "Resultado"} for h in hits]
        logger.info("chat_post kb_search hits=%s ids=%s", len(hits), [h.id for h in hits])

        if not hits:
            reply = (
                "No encontré esa información en mi base de conocimientos.\n"
                "Prueba con otras palabras (por ejemplo: servicios, automatización, EVE 360, metodología, etc.)."
            )
            logger.info("chat_post fin sin resultados")
        else:
            parts = []
            for h in hits:
                title = h.title or "Resultado"
                snippet = h.body.replace("\n", " ").strip()
                if len(snippet) > 350:
                    snippet = snippet[:350] + "…"
                parts.append(f"• {title}\n{snippet}")
            reply = "Encontré esto en la base de conocimientos:\n\n" + "\n\n".join(parts)
            logger.info("chat_post fin ok con %s fuentes", len(sources))

        return Response(
            {"session_id": session_id, "reply": reply, "sources": sources},
            status=status.HTTP_200_OK,
        )
