from rest_framework import serializers
from catalog.serializers import ProductListSerializer
from .models import Favorite


class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "product", "created_at")