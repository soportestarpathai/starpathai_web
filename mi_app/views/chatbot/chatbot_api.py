from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle

from mi_app.views.chatbot.services.kb_xml import search_kb


class ChatAPIView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "chat"

    MAX_MSG_LEN = 2000
    MAX_HISTORY_MSGS = 12  # 6 turnos (user+bot)

    def post(self, request, *args, **kwargs):
        session_id = request.data.get("session_id")
        message = (request.data.get("message") or "").strip()
        history = request.data.get("history") or []
        reset = bool(request.data.get("reset", False))

        if not session_id:
            return Response({"detail": "Falta session_id"}, status=status.HTTP_400_BAD_REQUEST)

        # Backend stateless: solo confirma reset (el frontend borra su history)
        if reset:
            return Response({"session_id": session_id, "reply": "🧹 Listo, reinicié la conversación."})

        if not message:
            return Response({"detail": "Mensaje vacío"}, status=status.HTTP_400_BAD_REQUEST)

        if len(message) > self.MAX_MSG_LEN:
            return Response({"detail": "Mensaje demasiado largo."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Validar history (no confiar en el cliente) ---
        safe_history = []
        if isinstance(history, list):
            for m in history[-self.MAX_HISTORY_MSGS:]:
                if not isinstance(m, dict):
                    continue
                role = m.get("role")
                content = (m.get("content") or "").strip()
                if role not in ("user", "bot"):
                    continue
                if not content:
                    continue
                safe_history.append({"role": role, "content": content[:self.MAX_MSG_LEN]})

        # --- Buscar en XML ---
        hits = search_kb(message, limit=3)

        sources = [{"id": h.id, "title": h.title or "Resultado"} for h in hits]

        if not hits:
            reply = (
                "No encontré esa información en mi base de conocimientos.\n"
                "Prueba con otras palabras (por ejemplo: servicios, automatización, EVE 360, metodología, etc.)."
            )
        else:
            parts = []
            for h in hits:
                title = h.title or "Resultado"
                snippet = h.body.replace("\n", " ").strip()
                if len(snippet) > 350:
                    snippet = snippet[:350] + "…"
                parts.append(f"• {title}\n{snippet}")

            reply = "Encontré esto en la base de conocimientos:\n\n" + "\n\n".join(parts)

        return Response(
            {"session_id": session_id, "reply": reply, "sources": sources},
            status=status.HTTP_200_OK
        )

