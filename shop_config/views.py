from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import SiteConfig


class SiteConfigView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        config = SiteConfig.load()
        return Response({
            "channel_url": config.channel_url,
            "support_url": config.support_url
        })
