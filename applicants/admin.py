from django.contrib import admin
from .models import Applicant

@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    # What columns to show in the list
    list_display = [
        "full_name", 
        "passport_number", 
        "destination_country", 
        "visa_type", 
        "status", 
        "partner", 
        "created_at"
    ]
    
    # Filters on the right side
    list_filter = ["status", "visa_type", "destination_country", "partner", "gender"]
    
    # Search bar config (Now includes passport number!)
    search_fields = ["full_name", "email", "phone", "passport_number", "partner__company_name"]
    
    # Use a magnifying glass for selecting partners (good if you have 100+ partners)
    raw_id_fields = ["partner"]
    
    readonly_fields = ["created_at", "updated_at"]

    # Organize the form into logical groups
    fieldsets = (
        ("Partner & Status", {
            "fields": ("partner", "status")
        }),
        ("Identity", {
            "fields": ("full_name", "gender", "date_of_birth", "marital_status", "nationality")
        }),
        ("Passport Details", {
            "fields": ("passport_number", "passport_issue_date", "passport_expiry_date", "place_of_birth")
        }),
        ("Contact Info", {
            "fields": ("phone", "email", "address")
        }),
        ("Travel Plans", {
            "fields": ("destination_country", "visa_type", "travel_date", "return_date")
        }),
        ("Dynamic Data", {
            "classes": ("collapse",),  # Hide by default to keep UI clean
            "fields": ("extra_data", "notes")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )