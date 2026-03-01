from decimal import Decimal
from rest_framework import serializers

from .models import Cart, CartItem

AVAILABLE_CURRENCIES = {"rub", "kzt", "byn"}


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source="variant.product.id", read_only=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    color = serializers.CharField(source="variant.color_name", read_only=True)
    size = serializers.CharField(source="variant.size", read_only=True)

    product_price = serializers.SerializerMethodField()
    product_image_url = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    is_available = serializers.SerializerMethodField()
    availability_message = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "variant",
            "product_id",
            "product_name",
            "product_price",
            "product_image_url",
            "color",
            "size",
            "quantity",
            "total_price",
            "is_available",
            "availability_message",
        ]

    def _get_price(self, product):
        currency = self.context.get("currency", "rub")

        if currency not in AVAILABLE_CURRENCIES:
            currency = "rub"

        if currency == "kzt":
            return product.price_kzt
        if currency == "byn":
            return product.price_byn

        return product.price_rub

    def get_is_available(self, obj):
        product = obj.variant.product

        return product.is_visible and obj.variant.stock > 0

    def get_availability_message(self, obj):
        product = obj.variant.product

        if not product.is_visible:
            return "Товар на текущий момент недоступен"

        if obj.variant.stock <= 0:
            return "Товар закончился на складе"

        return None

    def get_product_price(self, obj):
        return self._get_price(obj.variant.product)

    def get_total_price(self, obj):
        if not self.get_is_available(obj):
            return Decimal("0.00")

        price = self._get_price(obj.variant.product)
        return price * obj.quantity

    def get_product_image_url(self, obj):
        request = self.context.get("request")

        if obj.variant.product.main_image and request:
            return request.build_absolute_uri(
                obj.variant.product.main_image.url
            )

        return None


class CartSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "total_price"]

    def get_items(self, obj):
        queryset = obj.items.select_related("variant__product").order_by("id")

        serializer = CartItemSerializer(
            queryset,
            many=True,
            context=self.context
        )

        return serializer.data

    def get_total_price(self, obj):
        currency = self.context.get("currency", "rub")

        total = Decimal("0.00")

        queryset = obj.items.select_related("variant__product")

        for item in queryset:
            product = item.variant.product

            if not product.is_visible:
                continue

            if item.variant.stock <= 0:
                continue

            if currency == "kzt":
                price = product.price_kzt
            elif currency == "byn":
                price = product.price_byn
            else:
                price = product.price_rub

            total += price * item.quantity

        return total


class AddToCartSerializer(serializers.Serializer):
    variant = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=100)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=100)