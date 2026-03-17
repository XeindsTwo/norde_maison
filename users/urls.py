from django.urls import path
from .views import (
    RegisterView, LoginView, MeView, LogoutView,
    ConfirmEmailView, ChangePasswordView, UserOrderHistoryView,
    PasswordResetView, PasswordResetConfirmView
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("me/", MeView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("confirm/<str:token>/", ConfirmEmailView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
    path("password-reset/", PasswordResetView.as_view()),
    path("password-reset-confirm/<str:token>/", PasswordResetConfirmView.as_view()),
    path("orders/", UserOrderHistoryView.as_view(), name="profile-orders"),
]
