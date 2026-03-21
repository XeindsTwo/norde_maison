from decimal import Decimal
from django.db import transaction
from django.http import HttpResponse
import json
import yookassa
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from cart.models import Cart
from shop_config.models import DeliveryRegion
from .models import Order, OrderItem, OrderStatus
from .serializers import CheckoutSerializer, OrderSerializer, OrderPreviewSerializer
from .utils.yookassa import create_payment
from .utils.exchange_rates import convert_to_rub
from django.utils import timezone
from datetime import timedelta
import threading


def get_delivery_price(region, delivery_method, total_price_rub, currency):
    if delivery_method == "cdek_pvz":
        price_field = "cdek_pvz_price"
        free_from_field = "cdek_pvz_free_from"
    else:
        price_field = "cdek_courier_price"
        free_from_field = "cdek_courier_free_from"

    price = getattr(region, price_field)
    free_from = getattr(region, free_from_field)
    return Decimal("0.00") if total_price_rub >= free_from else price


def check_payment_status(payment_id):
    payment = yookassa.Payment.find_one(payment_id)
    return payment.status == "succeeded"


class CheckoutPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user

        currency = data["currency"]
        country = data["country"]
        delivery_method = data["delivery_method"]

        cart = Cart.objects.prefetch_related("items__variant__product").filter(user=user).first()
        if not cart or not cart.items.exists():
            return Response({"detail": "Корзина пуста"}, status=400)

        total_price_rub = Decimal("0")
        snapshot_buffer = []

        for item in cart.items.select_related("variant__product"):
            variant = item.variant
            product = variant.product
            if not product.is_visible or variant.stock < item.quantity:
                continue

            if currency == "kzt":
                price_rub = convert_to_rub(product.price_kzt, "kzt")
            elif currency == "byn":
                price_rub = convert_to_rub(product.price_byn, "byn")
            else:
                price_rub = product.price_rub

            total_price_rub += price_rub * item.quantity
            snapshot_buffer.append({
                "variant": variant,
                "product_name": product.name,
                "color": variant.color_name,
                "size": variant.size,
                "quantity": item.quantity,
                "price": price_rub,
            })

        if not snapshot_buffer:
            return Response({"detail": "Нет доступных товаров для оформления"}, status=400)

        try:
            region = DeliveryRegion.objects.get(code=country)
        except DeliveryRegion.DoesNotExist:
            return Response({"detail": "Регион не найден"}, status=400)

        delivery_price_rub = get_delivery_price(region, delivery_method, total_price_rub, currency)

        order = Order.objects.create(
            user=user,
            status=OrderStatus.PENDING,
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
            total_price=total_price_rub + delivery_price_rub,
            delivery_price=delivery_price_rub,
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

        payment = create_payment(order)
        order.payment_id = payment.id
        order.save(update_fields=["payment_id"])

        return Response({
            "payment_url": payment.confirmation.confirmation_url,
            "order_id": order.id,
            "order_number": order.order_number,
            "payment_id": payment.id
        })


class YookassaWebhookView(APIView):
    @method_decorator(csrf_exempt, name='dispatch')
    def post(self, request):
        data = json.loads(request.body)
        event = data.get("event")
        payment = data.get("object", {})

        if event == "payment.succeeded":
            payment_id = payment.get("id")
            try:
                order = Order.objects.get(payment_id=payment_id, status=OrderStatus.PENDING)
                order.status = OrderStatus.ASSEMBLY
                order.payment_verified = True
                order.save()

                from .signals import _send_order_email_async, _send_tg_notification_async
                import threading

                threading.Thread(target=_send_order_email_async, args=(order,), daemon=True).start()
                threading.Thread(target=_send_tg_notification_async, args=(order,), daemon=True).start()
            except Order.DoesNotExist:
                pass

        return HttpResponse(status=200)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user

        currency = data["currency"]
        country = data["country"]
        delivery_method = data["delivery_method"]

        cart = Cart.objects.prefetch_related("items__variant__product").filter(user=user).first()
        if not cart or not cart.items.exists():
            return Response({"detail": "Корзина пуста"}, status=400)

        total_price_rub = Decimal("0")
        snapshot_buffer = []

        for item in cart.items.select_related("variant__product"):
            variant = item.variant
            product = variant.product
            if not product.is_visible or variant.stock < item.quantity:
                continue

            if currency == "kzt":
                price_rub = convert_to_rub(product.price_kzt, "kzt")
            elif currency == "byn":
                price_rub = convert_to_rub(product.price_byn, "byn")
            else:
                price_rub = product.price_rub

            total_price_rub += price_rub * item.quantity
            snapshot_buffer.append({
                "variant": variant,
                "product_name": product.name,
                "color": variant.color_name,
                "size": variant.size,
                "quantity": item.quantity,
                "price": price_rub,
            })

        if not snapshot_buffer:
            return Response({"detail": "Нет доступных товаров для оформления"}, status=400)

        try:
            region = DeliveryRegion.objects.get(code=country)
        except DeliveryRegion.DoesNotExist:
            return Response({"detail": "Регион не найден"}, status=400)

        delivery_price_rub = get_delivery_price(region, delivery_method, total_price_rub, currency)

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
            total_price=total_price_rub + delivery_price_rub,
            delivery_price=delivery_price_rub,
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

        delivery_regions = DeliveryRegion.objects.all()
        serializer = OrderPreviewSerializer({
            "items": items_data,
            "subtotal_rub": subtotal_rub,
            "subtotal_kzt": subtotal_kzt,
            "subtotal_byn": subtotal_byn,
            "delivery_regions": delivery_regions,
            "delivery_method_choices": ["cdek_pvz", "cdek_courier"],
        })
        return Response(serializer.data)


def check_payment_status(payment_id):
    payment = yookassa.Payment.find_one(payment_id)
    return payment.status == "succeeded"


class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        status = check_payment_status(payment_id)
        if status:
            try:
                order = Order.objects.get(payment_id=payment_id, status=OrderStatus.PENDING)
                order.status = OrderStatus.ASSEMBLY
                order.payment_verified = True
                order.notified = True
                order.save(update_fields=['status', 'payment_verified', 'notified'])

                threading.Thread(target=_send_order_email_async, args=(order,), daemon=True).start()
                threading.Thread(target=_send_tg_notification_async, args=(order,), daemon=True).start()

            except Order.DoesNotExist:
                pass
        return Response({"succeeded": status})


class OrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        try:
            order = Order.objects.get(user=request.user, order_number=order_number)
            return Response({"status": order.status})
        except Order.DoesNotExist:
            return Response({"status": "not_found"}, status=404)


class CurrentPendingOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        order = Order.objects.filter(
            user=user,
            status=OrderStatus.PENDING,
            created_at__gte=now - timedelta(minutes=10),
            payment_verified=False
        ).first()

        if not order:
            return Response({"has_pending": False})

        expires_in_seconds = max(0, int((order.created_at + timedelta(minutes=10) - now).total_seconds()))

        payment_url = None
        if order.payment_id:
            try:
                payment = yookassa.Payment.find_one(order.payment_id)
                payment_url = payment.confirmation.confirmation_url
            except:
                payment = create_payment(order)
                order.payment_id = payment.id
                order.save(update_fields=["payment_id"])
                payment_url = payment.confirmation.confirmation_url

        return Response({
            "has_pending": True,
            "order_number": order.order_number,
            "payment_id": order.payment_id,
            "total_price": order.total_price,
            "created_at": order.created_at,
            "expires_in_seconds": expires_in_seconds,
            "payment_url": payment_url
        })
