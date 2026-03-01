from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="variant.product.name",
        read_only=True
    )

    product_price = serializers.DecimalField(
        source="variant.product.price_rub",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    product_image = serializers.ImageField(
        source="variant.product.main_image",
        read_only=True
    )

    color = serializers.CharField(
        source="variant.color_name",
        read_only=True
    )

    size = serializers.CharField(
        source="variant.size",
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            "id",
            "variant",
            "product_name",
            "product_price",
            "product_image",
            "color",
            "size",
            "quantity",
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "total_price"]

    def get_total_price(self, obj):
        return sum(
            item.variant.product.price_rub * item.quantity
            for item in obj.items.select_related("variant__product")
        )


class AddToCartSerializer(serializers.Serializer):
    variant = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=100)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=100)