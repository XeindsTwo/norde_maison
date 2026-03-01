from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from catalog.models import Product
from .models import Favorite
from .serializers import FavoriteSerializer


class FavoriteToggleView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        product_id = request.data.get("product_id")

        if not product_id:
            return Response(
                {"detail": "product_id обязателен"},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = Product.objects.filter(
            id=product_id,
            is_visible=True
        ).first()

        if not product:
            return Response(
                {"detail": "Товар не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            favorite.delete()
            return Response({
                "product_id": product_id,
                "favorite": False
            })

        return Response({
            "product_id": product_id,
            "favorite": True
        })


class FavoriteDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        Favorite.objects.filter(
            user=request.user,
            product_id=product_id
        ).delete()

        return Response({"success": True})


class FavoriteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Favorite.objects.filter(
            user=request.user
        ).select_related(
            "product",
            "product__subcategory",
            "product__subcategory__category"
        ).prefetch_related(
            "product__images",
            "product__variants"
        ).order_by("-created_at")

        serializer = FavoriteSerializer(
            qs,
            many=True,
            context={"request": request}
        )

        return Response({
            "data": serializer.data
        })