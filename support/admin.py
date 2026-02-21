from django.contrib import admin
from .models import Ticket, TicketMessage


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ["created_at"]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["id", "partner", "subject", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["subject", "partner__company_name"]
    raw_id_fields = ["partner"]
    inlines = [TicketMessageInline]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "ticket", "author", "is_staff_reply", "created_at"]
    raw_id_fields = ["ticket", "author"]
