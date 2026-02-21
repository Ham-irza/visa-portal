from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "applicant", "amount", "currency", "status", "payment_date", "created_at"]
    list_filter = ["status", "currency"]
    search_fields = ["applicant__full_name", "invoice_number"]
    raw_id_fields = ["applicant"]
    readonly_fields = ["created_at", "updated_at"]
