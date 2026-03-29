import uuid

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import UserProfile, PasswordResetToken


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Профиль"
    fk_name = "user"


class UserAdmin(BaseUserAdmin):
    save_on_top = True
    inlines = [UserProfileInline]
    readonly_fields = ("password",)

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "is_superuser",
        "reset_password_action",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
    )

    fieldsets = (
        (None, {"fields": ("username",)}),
        (_("Персональная информация"), {"fields": ("first_name", "last_name", "email")}),
        (_("Статус аккаунта"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2"),
        }),
        (_("Права доступа"), {
            "fields": ("is_staff", "is_superuser", "groups"),
        }),
    )

    ordering = ("username",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:user_id>/send-reset-password/",
                self.admin_site.admin_view(self.send_reset_password_view),
                name="auth_user_send_reset_password",
            ),
        ]
        return custom_urls + urls

    def reset_password_action(self, obj):
        url = reverse("admin:auth_user_send_reset_password", args=[obj.pk])
        return format_html('<a class="button" href="{}">Сброс пароля</a>', url)

    reset_password_action.short_description = "Действие"

    def send_reset_password_view(self, request, user_id):
        user = User.objects.get(pk=user_id)

        try:
            self.send_reset_email(user)
            self.message_user(request, "Письмо для сброса пароля отправлено.", level=messages.SUCCESS)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            self.message_user(request, f"Не удалось отправить письмо: {e}", level=messages.ERROR)

        return HttpResponseRedirect(reverse("admin:auth_user_change", args=[user_id]))

    def send_reset_email(self, user):
        with transaction.atomic():
            token_obj, _ = PasswordResetToken.objects.update_or_create(
                user=user,
                defaults={"token": uuid.uuid4(), "used_at": None}
            )

        reset_url = f"{settings.SITE_URL_CLIENT}/?reset_token={token_obj.token}"
        context = {
            "first_name": user.first_name,
            "reset_url": reset_url,
        }

        html_body = render_to_string("users/password_reset.html", context)

        email = EmailMultiAlternatives(
            subject="Сброс пароля — Norde Maison",
            body="Перейдите по ссылке для смены пароля.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)