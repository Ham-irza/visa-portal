from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Partner


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active"]
    search_fields = ["email", "username"]
    ordering = ["-date_joined"]
    fieldsets = BaseUserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ["company_name", "user", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["company_name", "user__email"]
    raw_id_fields = ["user"]
