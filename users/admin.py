from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Профиль"
    fk_name = "user"


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "is_superuser",
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
        (None, {
            "fields": ("username", "password")
        }),

        (_("Персональная информация"), {
            "fields": ("first_name", "last_name", "email")
        }),

        (_("Статус аккаунта"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
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


admin.site.unregister(User)
admin.site.register(User, UserAdmin)