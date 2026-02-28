from django.contrib.auth.models import User
from rest_framework import serializers, status
from django.contrib.auth import password_validation
from django.core import exceptions
from rest_framework.validators import UniqueValidator
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("phone", "tg_username", "address")


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "profile"
        )


class RegisterSerializer(serializers.ModelSerializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(
        required=True,
        error_messages={
            "blank": "Поле имени обязательно",
            "required": "Поле имени обязательно"
        }
    )

    last_name = serializers.CharField(
        required=True,
        error_messages={
            "blank": "Поле фамилии обязательно",
            "required": "Поле фамилии обязательно"
        }
    )

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "first_name",
            "last_name"
        )

    def validate_email(self, value):
        value = value.lower()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email уже зарегистрирован")

        return value

    def validate_first_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Введите имя")
        return value

    def validate_last_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Введите фамилию")
        return value

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        email = validated_data["email"].lower()

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
            is_active=False
        )

        return user