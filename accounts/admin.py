# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Usa el admin estándar extendido para mostrar email/username/id.
    """
    list_display = ("username", "email", "id", "is_staff", "is_active")
    ordering = ("username",)
