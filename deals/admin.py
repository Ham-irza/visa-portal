"""
Admin configuration for Deals.
"""
from django.contrib import admin
from .models import Deal, DealNote


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['id', 'deal_id', 'applicant', 'partner', 'status', 'payment_status', 'amount', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['applicant__full_name', 'applicant__email', 'partner__company_name']
    readonly_fields = ['deal_id', 'created_at', 'updated_at']
    fieldsets = [
        ('Basic Info', {
            'fields': ['deal_id', 'applicant', 'partner', 'assigned_to']
        }),
        ('Deal Details', {
            'fields': ['visa_type', 'destination_country', 'status', 'payment_status']
        }),
        ('Financial', {
            'fields': ['amount', 'paid_amount', 'currency']
        }),
        ('Notes', {
            'fields': ['partner_notes', 'internal_notes']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(DealNote)
class DealNoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'deal', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['deal__id', 'content']
