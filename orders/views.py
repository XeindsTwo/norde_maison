from decimal import Decimal
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cart.models import Cart
from shop_config.models import DeliveryRegion

from .models import Order, OrderItem, OrderStatus
from .serializers import CheckoutSerializer, OrderSerializer, OrderPreviewSerializer

FREE_DELIVERY_THRESHOLD = Decimal("6000")


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user

        cart = Cart.objects.prefetch_related("items__variant__product").filter(user=user).first()
        if not cart or not cart.items.exists():
            return Response({"detail": "Корзина пуста"}, status=400)

        total_price = Decimal("0")
        snapshot_buffer = []

        for item in cart.items.select_related("variant__product"):
            variant = item.variant
            product = variant.product
            if not product.is_visible or variant.stock < item.quantity:
                continue
            price = product.price_rub
            total_price += price * item.quantity
            snapshot_buffer.append({
                "variant": variant,
                "product_name": product.name,
                "color": variant.color_name,
                "size": variant.size,
                "quantity": item.quantity,
                "price": price,
            })

        if not snapshot_buffer:
            return Response({"detail": "Нет доступных товаров для оформления"}, status=400)

        delivery_price = data["delivery_price"]
        if total_price >= FREE_DELIVERY_THRESHOLD:
            delivery_price = Decimal("0")

        order = Order.objects.create(
            user=user,
            status=OrderStatus.ASSEMBLY,
            country=data["country"],
            delivery_method=data["delivery_method"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            middle_name=data.get("middle_name", ""),
            phone=data.get("phone", ""),
            telegram=data.get("telegram", ""),
            address=data.get("address", ""),
            delivery_extra=data.get("delivery_extra", None),
            comment=data.get("comment", ""),
            total_price=total_price + delivery_price,
            delivery_price=delivery_price,
        )

        for item_data in snapshot_buffer:
            OrderItem.objects.create(
                order=order,
                variant=item_data["variant"],
                product_name=item_data["product_name"],
                color=item_data["color"],
                size=item_data["size"],
                quantity=item_data["quantity"],
                price_snapshot=item_data["price"],
            )
            item_data["variant"].stock -= item_data["quantity"]
            item_data["variant"].save()

        cart.items.all().delete()
        return Response({"success": True, "order_number": order.order_number})


class OrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related("items").order_by("-created_at")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class OrderPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        cart = Cart.objects.prefetch_related("items__variant__product").filter(user=user).first()
        if not cart or not cart.items.exists():
            return Response({"detail": "Корзина пуста"}, status=400)

        items_data = []
        subtotal_rub = Decimal("0")
        subtotal_kzt = Decimal("0")
        subtotal_byn = Decimal("0")

        for item in cart.items.select_related("variant__product"):
            variant = item.variant
            product = variant.product
            if not product.is_visible or variant.stock < item.quantity:
                continue
            subtotal_rub += product.price_rub * item.quantity
            subtotal_kzt += product.price_kzt * item.quantity
            subtotal_byn += product.price_byn * item.quantity
            items_data.append({
                "product_name": product.name,
                "color": variant.color_name,
                "size": variant.size,
                "quantity": item.quantity,
                "price_rub": product.price_rub,
                "price_kzt": product.price_kzt,
                "price_byn": product.price_byn,
                "image_url": request.build_absolute_uri(product.main_image.url) if product.main_image else None,
                "product_id": product.id
            })

        serializer = OrderPreviewSerializer({
            "items": items_data,
            "subtotal_rub": subtotal_rub,
            "subtotal_kzt": subtotal_kzt,
            "subtotal_byn": subtotal_byn,
            "delivery_regions": DeliveryRegion.objects.all(),
            "delivery_method_choices": ["cdek_pvz", "cdek_courier"],
        })
        return Response(serializer.data)