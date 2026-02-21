from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["id", "applicant", "document_type", "status", "uploaded_at"]
    list_filter = ["status", "document_type"]
    search_fields = ["applicant__full_name", "original_filename"]
    raw_id_fields = ["applicant"]
    readonly_fields = ["uploaded_at"]
