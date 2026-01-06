from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from mi_app.views.chatbot.services.kb_xml import get_item_by_id


class KBItemAPIView(APIView):
    """
    GET /api/kb/item/<item_id>/
    Devuelve el item del XML para mostrarlo como "fuente" en el frontend.
    """

    def get(self, request, item_id: str, *args, **kwargs):
        it = get_item_by_id(item_id)
        if not it:
            return Response({"detail": "Fuente no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "id": it.id,
                "title": it.title,
                "body": it.body,
                "tags": it.tags,
            },
            status=status.HTTP_200_OK,
        )
