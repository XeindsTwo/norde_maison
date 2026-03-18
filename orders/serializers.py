from rest_framework import serializers
from .models import Order, OrderItem
from shop_config.models import DeliveryRegion

class CheckoutSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    middle_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField()
    telegram = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField()
    delivery_method = serializers.CharField()
    delivery_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.ChoiceField(choices=['rub', 'kzt', 'byn'])
    comment = serializers.CharField(required=False, allow_blank=True)
    delivery_extra = serializers.DictField(required=False, allow_empty=True)
    address = serializers.CharField(required=False, allow_blank=True)

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
            "first_name", "last_name", "middle_name", "phone", "telegram",
            "address", "delivery_extra", "comment", "total_price",
            "delivery_price", "created_at", "items"
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
    product_id = serializers.IntegerField()
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

class OrderItemDetailSerializer(serializers.ModelSerializer):
    variant_id = serializers.IntegerField(source='variant.id')
    product_id = serializers.IntegerField(source='variant.product.id')
    product_name = serializers.CharField(source='variant.product.name')
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'product_id', 'product_name', 'variant_id', 'color', 'size',
            'quantity', 'price_snapshot', 'main_image'
        ]

    def get_main_image(self, obj):
        request = self.context.get("request")
        if obj.variant and obj.variant.product.main_image:
            url = obj.variant.product.main_image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(many=True, read_only=True)
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'created_at', 'total_price',
            'delivery_price', 'delivery_method', 'address', 'delivery_extra',
            'comment', 'items',
            'first_name', 'last_name', 'middle_name', 'phone', 'telegram'
        ]

    def get_created_at(self, obj):
        return obj.created_at.strftime("%d.%m.%y")