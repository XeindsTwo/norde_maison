from rest_framework import serializers
from .models import DeliveryRegion


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