from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

class LandingPage(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "landing/index.html"

    def get(self, request):
        return Response({"titulo": "StarpathAI"})

