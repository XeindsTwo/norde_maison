from rest_framework import serializers
from .models import Order, OrderItem
from shop_config.models import DeliveryRegion


class CheckoutSerializer(serializers.Serializer):
    country = serializers.CharField()
    delivery_method = serializers.CharField()
    address = serializers.CharField(required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)
    delivery_price = serializers.DecimalField(max_digits=12, decimal_places=2)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ("product_name", "color", "size", "quantity", "price_snapshot")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "order_number", "status", "country", "delivery_method",
            "address", "comment", "total_price", "delivery_price",
            "created_at", "items"
        )


class DeliveryRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryRegion
        fields = (
            "code",
            "cdek_pvz_price", "cdek_pvz_free_from",
            "cdek_courier_price", "cdek_courier_free_from",
            "cdek_pvz_price_kzt", "cdek_pvz_free_from_kzt",
            "cdek_courier_price_kzt", "cdek_courier_free_from_kzt",
            "cdek_pvz_price_byn", "cdek_pvz_free_from_byn",
            "cdek_courier_price_byn", "cdek_courier_free_from_byn",
        )


class OrderPreviewItemSerializer(serializers.Serializer):
    product_name = serializers.CharField()
    color = serializers.CharField()
    size = serializers.CharField()
    quantity = serializers.IntegerField()
    price_rub = serializers.DecimalField(max_digits=12, decimal_places=2)
    price_kzt = serializers.DecimalField(max_digits=12, decimal_places=2)
    price_byn = serializers.DecimalField(max_digits=12, decimal_places=2)
    image_url = serializers.CharField(allow_null=True)


class OrderPreviewSerializer(serializers.Serializer):
    items = OrderPreviewItemSerializer(many=True)
    subtotal_rub = serializers.DecimalField(max_digits=12, decimal_places=2)
    subtotal_kzt = serializers.DecimalField(max_digits=12, decimal_places=2)
    subtotal_byn = serializers.DecimalField(max_digits=12, decimal_places=2)
    delivery_regions = DeliveryRegionSerializer(many=True)
    delivery_method_choices = serializers.ListField(child=serializers.CharField())
