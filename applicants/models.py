"""
Applicant (client) model.
Includes comprehensive Visa fields and a JSONField for dynamic requirements.
"""
from django.db import models
from accounts.models import Partner

class Applicant(models.Model):
    # --- Status Choices ---
    STATUS_NEW = "new"
    STATUS_DOCS_PENDING = "docs_pending"
    STATUS_PROCESSING = "processing"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_COMPLETED = "completed"
    
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_DOCS_PENDING, "Docs Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_COMPLETED, "Completed"),
    ]

    # --- Gender & Marital Choices ---
    GENDER_MALE = "M"
    GENDER_FEMALE = "F"
    GENDER_OTHER = "O"
    GENDER_CHOICES = [
        (GENDER_MALE, "Male"),
        (GENDER_FEMALE, "Female"),
        (GENDER_OTHER, "Other"),
    ]

    MARITAL_SINGLE = "single"
    MARITAL_MARRIED = "married"
    MARITAL_DIVORCED = "divorced"
    MARITAL_WIDOWED = "widowed"
    MARITAL_CHOICES = [
        (MARITAL_SINGLE, "Single"),
        (MARITAL_MARRIED, "Married"),
        (MARITAL_DIVORCED, "Divorced"),
        (MARITAL_WIDOWED, "Widowed"),
    ]

    # --- Relationships ---
    # Partner may be null for individual applicants who register/login themselves.
    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="applicants",
        null=True,
        blank=True,
        help_text="The partner company that owns this applicant. Null for self-registered applicants."
    )

    # Link to a User when the applicant registers themself (individual flow).
    # This is optional and allows the user to log in and manage their own application.
    from django.conf import settings
    applicant_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='applicant_profiles',
        null=True,
        blank=True,
        help_text='If set, this User owns this applicant profile.'
    )

    # --- Basic Identity ---
    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default=GENDER_MALE)
    date_of_birth = models.DateField(null=True, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_CHOICES, default=MARITAL_SINGLE)
    
    # --- Contact Info ---
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True, help_text="Current residential address")
    
    # --- Passport Details ---
    passport_number = models.CharField(max_length=100, blank=True)
    passport_expiry_date = models.DateField(null=True, blank=True)
    passport_issue_date = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=100, blank=True)
    
    # --- Travel & Visa Info ---
    nationality = models.CharField(max_length=100, blank=True)
    destination_country = models.CharField(max_length=100, blank=True)
    visa_type = models.CharField(max_length=100, blank=True)  # e.g., "Tourist", "Business"
    travel_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)

    # --- System Fields ---
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_NEW)
    notes = models.TextField(blank=True)
    
    # --- The "Magic" Field (Dynamic Data) ---
    # Stores anything else: Father's Name, Mother's Name, Previous Visa #, etc.
    extra_data = models.JSONField(default=dict, blank=True, help_text="Dynamic fields for specific visa requirements")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "applicants"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["partner", "status"]),
            models.Index(fields=["partner", "passport_number"]), # Quick lookup by passport
            models.Index(fields=["partner", "created_at"]),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.passport_number} ({self.status})"