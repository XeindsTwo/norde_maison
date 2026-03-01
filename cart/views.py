from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from catalog.models import ProductVariant

from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)

MAX_QUANTITY_PER_VARIANT = 5


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        serializer = CartSerializer(cart)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        variant = get_object_or_404(ProductVariant, id=data["variant"])

        if variant.stock <= 0:
            return Response(
                {"detail": "Товар закончился на складе"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart, _ = Cart.objects.get_or_create(user=request.user)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={"quantity": data["quantity"]},
        )

        if not created:
            new_quantity = item.quantity + data["quantity"]

            if new_quantity > variant.stock:
                return Response(
                    {"detail": "Превышен остаток на складе"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if new_quantity > MAX_QUANTITY_PER_VARIANT:
                return Response(
                    {"detail": f"Максимум {MAX_QUANTITY_PER_VARIANT} единиц товара"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            item.quantity = new_quantity
            item.save()

            return Response(
                {"detail": "Количество товара обновлено"},
                status=status.HTTP_200_OK
            )

        if data["quantity"] > variant.stock:
            return Response(
                {"detail": "Превышен остаток на складе"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if data["quantity"] > MAX_QUANTITY_PER_VARIANT:
            return Response(
                {"detail": f"Максимум {MAX_QUANTITY_PER_VARIANT} единиц товара"},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.quantity = data["quantity"]
        item.save()

        return Response(
            {"detail": "Товар добавлен в корзину"},
            status=status.HTTP_201_CREATED
        )


class UpdateCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item = get_object_or_404(
            CartItem,
            pk=pk,
            cart__user=request.user
        )

        new_quantity = serializer.validated_data["quantity"]

        variant_stock = item.variant.stock

        if new_quantity > variant_stock:
            return Response(
                {"detail": "Превышен остаток на складе"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_quantity > MAX_QUANTITY_PER_VARIANT:
            return Response(
                {"detail": f"Максимум {MAX_QUANTITY_PER_VARIANT} единиц товара"},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.quantity = new_quantity
        item.save()

        return Response(
            {"detail": "Количество обновлено"},
            status=status.HTTP_200_OK
        )


class DeleteCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        item = get_object_or_404(
            CartItem,
            pk=pk,
            cart__user=request.user
        )

        item.delete()

        return Response(
            {"detail": "Товар удалён"},
            status=status.HTTP_204_NO_CONTENT
        )
