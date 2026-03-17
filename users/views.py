import uuid
import threading
from django.db import transaction
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework import generics, permissions, status
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.shortcuts import render
from .models import EmailActivation, UserProfile
from .serializers import (
    RegisterSerializer, UserSerializer, ProfileUpdateSerializer, ChangePasswordSerializer
)
from orders.models import Order
from orders.serializers import OrderDetailSerializer


def format_validation_error(error):
    if isinstance(error, dict):
        value = next(iter(error.values()))
        if isinstance(value, list):
            return str(value[0])

    if hasattr(error, "messages"):
        return error.messages[0]

    text = str(error)

    text = text.replace(
        "Ensure this value has at least 8 characters",
        "В пароле должно быть минимум 8 символов"
    )

    if "too common" in text.lower():
        return "Пароль слишком простой"

    if "numeric" in text.lower():
        return "Пароль не должен состоять только из цифр"

    return text


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def send_activation_email_async(self, user, activation_token):
        """
        Отправка email в отдельном потоке (не блокирует HTTP request).
        """

        try:
            confirm_url = f"{settings.SITE_URL}/api/auth/confirm/{activation_token}/"

            html_message = render_to_string(
                "users/welcome_email.html",
                {
                    "first_name": user.first_name,
                    "confirm_url": confirm_url
                }
            )

            email = EmailMultiAlternatives(
                subject="Подтверждение регистрации",
                body="Подтвердите email",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )

            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)

        except Exception:
            pass

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = None
        activation = None

        with transaction.atomic():
            user = serializer.save()

            activation = EmailActivation.objects.get(user=user)

        if user and activation:
            thread = threading.Thread(
                target=self.send_activation_email_async,
                args=(user, activation.token),
            )
            thread.daemon = True
            thread.start()

        return Response(
            {
                "success": True,
                "message": "Письмо подтверждения отправлено"
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"detail": "Заполните поля"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Неверный email или пароль"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Неверный email или пароль"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.is_active:
            return Response(
                {"detail": "Подтвердите email, прежде чем войти в аккаунт"},
                status=status.HTTP_403_FORBIDDEN
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user": UserSerializer(user).data
        })


class ConfirmEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):

        try:
            activation = EmailActivation.objects.get(
                token=uuid.UUID(token)
            )

            if activation.is_expired():
                return render(request, "users/email_expired.html")

            user = activation.user
            user.is_active = True
            user.save()

            activation.delete()

            return render(request, "users/email_confirm_success.html")

        except (EmailActivation.DoesNotExist, ValueError):
            return render(request, "users/email_not_found.html")


class UserOrderHistoryView(ListAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items__variant__product'
        ).order_by('-created_at')[:10]


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        user = request.user

        profile, _ = UserProfile.objects.get_or_create(user=user)

        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)

        user.save()

        profile_serializer = ProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True
        )

        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        return Response({
            "success": True,
            "profile": profile_serializer.data
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.auth:
            request.auth.delete()
        return Response({"detail": "Logout success"})


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not user.check_password(old_password):
            return Response(
                {"detail": "Неверный текущий пароль"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        current_token = request.auth

        Token.objects.filter(user=user).exclude(
            key=current_token.key if current_token else ""
        ).delete()

        if current_token:
            Token.objects.filter(key=current_token.key).delete()

        new_token = Token.objects.create(user=user)

        html_message = render_to_string(
            "users/password_changed.html",
            {
                "first_name": user.first_name,
            }
        )

        email = EmailMultiAlternatives(
            subject="Пароль успешно изменён",
            body="Пароль был изменён",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )

        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=True)

        return Response({
            "success": True,
            "token": new_token.key
        })


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower()

        try:
            user = User.objects.get(username__iexact=email)
            if not user.is_active:
                return Response({"detail": "Сначала подтвердите email"}, status=status.HTTP_400_BAD_REQUEST)

            activation, _ = EmailActivation.objects.get_or_create(user=user)
            activation.token = uuid.uuid4()
            activation.save()

            thread = threading.Thread(
                target=self.send_reset_email_async,
                args=(user, str(activation.token))
            )
            thread.daemon = True
            thread.start()

            return Response({
                "message": "Инструкции отправлены на email",
                "reset_token": str(activation.token)  # Frontend bonus
            })
        except User.DoesNotExist:
            return Response({"message": "Инструкции отправлены на email"})

    def send_reset_email_async(self, user, token):
        try:
            reset_url = f"{settings.SITE_URL_CLIENT}/?reset_token={token}"
            html_message = render_to_string("users/password_reset.html", {
                "first_name": user.first_name,
                "reset_url": reset_url
            })

            email = EmailMultiAlternatives(
                subject="Сброс пароля — Norde Maison",
                body="Перейдите по ссылке для сброса пароля",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=True)
        except Exception:
            pass


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, token):
        try:
            activation = EmailActivation.objects.get(token=uuid.UUID(token))
            if activation.is_expired():
                return Response({"detail": "Ссылка истекла"}, status=status.HTTP_400_BAD_REQUEST)

            new_password = request.data.get('new_password')
            if not new_password:
                return Response({"detail": "Укажите новый пароль"}, status=status.HTTP_400_BAD_REQUEST)

            validate_password(new_password)

            user = activation.user
            user.set_password(new_password)
            user.save()

            thread = threading.Thread(
                target=self.send_password_changed_email_async,
                args=(user,)
            )
            thread.daemon = True
            thread.start()

            Token.objects.filter(user=user).delete()
            activation.delete()

            return Response({"message": "Пароль успешно сброшен"})
        except (EmailActivation.DoesNotExist, ValueError, ValidationError):
            return Response({"detail": "Неверная ссылка"}, status=status.HTTP_400_BAD_REQUEST)

    def send_password_changed_email_async(self, user):
        try:
            html_message = render_to_string("users/password_changed.html", {
                "first_name": user.first_name
            })
            email = EmailMultiAlternatives(
                "Пароль успешно изменён — Norde Maison",
                "Пароль от вашего аккаунта обновлён",
                settings.DEFAULT_FROM_EMAIL, [user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=True)
        except Exception:
            pass