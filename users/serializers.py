from django.contrib.auth.models import User
from rest_framework import serializers
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

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "first_name",
            "last_name"
        )

    def validate(self, data):

        password = data.get("password")

        user = User(
            username=data.get("username"),
            email=data.get("email")
        )

        try:
            password_validation.validate_password(password, user)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({
                "password": list(e.messages)
            })

        return data

    def create(self, validated_data):

        password = validated_data.pop("password")

        user = User.objects.create(
            **validated_data,
            is_active=False
        )

        user.set_password(password)
        user.save()

        return user