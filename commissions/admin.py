from django.contrib import admin
from .models import Commission


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ["id", "applicant", "amount", "currency", "status", "paid_at", "created_at"]
    list_filter = ["status"]
    search_fields = ["applicant__full_name", "payout_reference"]
    raw_id_fields = ["applicant"]
    readonly_fields = ["created_at", "updated_at"]
