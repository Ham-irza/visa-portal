"""
Document uploads per applicant.
Security-hardened with UUIDs and File Validation.
"""
import os
import uuid
from django.db import models
from django.core.validators import FileExtensionValidator
from applicants.models import Applicant

def document_upload_path(instance, filename):
    """
    Store under media/documents/<applicant_uuid>/<random_uuid>.<ext>
    This obfuscates the filename so internal naming conventions are not leaked.
    """
    ext = os.path.splitext(filename)[1].lower()
    # If no extension, force .bin to prevent execution
    if not ext:
        ext = ".bin"
    
    # Generate a random filename, keep the extension
    safe_name = f"{uuid.uuid4().hex}{ext}"
    
    # Return path: documents/APPLICANT_ID/SAFE_NAME
    return os.path.join("documents", str(instance.applicant.id), safe_name)

class Document(models.Model):
    # --- Security: UUID Primary Key ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- Status Choices ---
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    # --- Document Types ---
    DOC_TYPE_PASSPORT = "passport"
    DOC_TYPE_PHOTO = "photo"
    DOC_TYPE_BANK = "bank_statement"
    DOC_TYPE_TICKET = "ticket"
    DOC_TYPE_INSURANCE = "insurance"
    DOC_TYPE_OTHER = "other"
    
    DOC_TYPE_CHOICES = [
        (DOC_TYPE_PASSPORT, "Passport Scan"),
        (DOC_TYPE_PHOTO, "Passport Photo"),
        (DOC_TYPE_BANK, "Bank Statement"),
        (DOC_TYPE_TICKET, "Flight Ticket"),
        (DOC_TYPE_INSURANCE, "Travel Insurance"),
        (DOC_TYPE_OTHER, "Other"),
    ]

    # --- Relationships ---
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name="documents",
        null=False,
        blank=False,
        help_text="The applicant this document belongs to."
    )

    # --- File Data ---
    document_type = models.CharField(max_length=50, choices=DOC_TYPE_CHOICES, default=DOC_TYPE_OTHER)
    
    file = models.FileField(
        upload_to=document_upload_path,
        max_length=500,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            )
        ],
        help_text="Allowed formats: PDF, JPG, PNG, DOC, DOCX"
    )
    
    original_filename = models.CharField(max_length=255, blank=True, help_text="Original name of the uploaded file")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "documents"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["applicant", "status"]),
            models.Index(fields=["applicant", "document_type"]),
        ]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.applicant.full_name}"

    def save(self, *args, **kwargs):
        # Auto-save the original filename if it's a new upload
        if self.file and not self.original_filename:
            self.original_filename = self.file.name
        super().save(*args, **kwargs)


class ServiceType(models.Model):
    """Represents a service or visa type (e.g. M Visa, Z Visa, Business Registration)."""
    key = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "service_types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class RequiredDocument(models.Model):
    """A single required document for a given ServiceType."""
    service = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name="requirements")
    title = models.CharField(max_length=255)
    optional = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "service_required_documents"
        ordering = ["service_id", "order"]

    def __str__(self):
        return f"{self.service.name}: {self.title}"