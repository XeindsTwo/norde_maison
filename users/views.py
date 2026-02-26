import uuid

from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.shortcuts import render

from .serializers import RegisterSerializer, UserSerializer
from .models import EmailActivation


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):

        user = serializer.save()

        activation = EmailActivation.objects.get(user=user)

        confirm_url = f"{settings.SITE_URL}/api/auth/confirm/{activation.token}/"

        html_message = render_to_string(
            "users/welcome_email.html",
            {
                "first_name": user.first_name,
                "confirm_url": confirm_url
            }
        )

        email = EmailMultiAlternatives(
            subject="Добро пожаловать",
            body="Подтвердите email",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )

        email.attach_alternative(html_message, "text/html")
        email.send()

        return user


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):

        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Неверные данные"},
                status=400
            )

        user = authenticate(
            request,
            username=user.username,
            password=password
        )

        if not user:
            return Response(
                {"detail": "Неверные данные"},
                status=400
            )

        if not user.is_active:
            return Response(
                {"detail": "Email не подтверждён"},
                status=403
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


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):

    def post(self, request):

        if request.auth:
            request.auth.delete()

        return Response({"detail": "Logout success"})