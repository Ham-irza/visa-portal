"""
Deals model - represents visa application cases/orders for applicants.
"""
from django.db import models
from applicants.models import Applicant
from accounts.models import Partner, User


class Deal(models.Model):
    """
    Represents each visa application case/order for an applicant.
    Links to Applicant and Partner for data isolation.
    """
    # --- Status Choices ---
    STATUS_NEW = "new"
    STATUS_DOCS_PENDING = "docs_pending"
    STATUS_PROCESSING = "processing"
    STATUS_APPROVED = "approved"
    STATUS_COMPLETED = "completed"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"
    
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_DOCS_PENDING, "Docs Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    # --- Payment Status Choices ---
    PAYMENT_UNPAID = "unpaid"
    PAYMENT_PARTIAL = "partial"
    PAYMENT_PAID = "paid"
    
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_UNPAID, "Unpaid"),
        (PAYMENT_PARTIAL, "Partial"),
        (PAYMENT_PAID, "Paid"),
    ]

    # --- Relationships ---
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name="deals",
        help_text="The applicant this deal belongs to"
    )
    
    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="deals",
        help_text="Partner who created this deal"
    )
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_deals",
        help_text="Staff member assigned to this deal"
    )

    # --- Deal Fields ---
    visa_type = models.CharField(max_length=100, blank=True, help_text="e.g., Tourist, Business, Work")
    destination_country = models.CharField(max_length=100, blank=True)
    
    # Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_NEW)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_UNPAID)
    
    # Amounts
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    
    # Notes
    partner_notes = models.TextField(blank=True, help_text="Notes visible to partner")
    internal_notes = models.TextField(blank=True, help_text="Internal notes (staff only)")
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "deals"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["partner", "status"]),
            models.Index(fields=["partner", "payment_status"]),
            models.Index(fields=["partner", "created_at"]),
            models.Index(fields=["applicant"]),
        ]

    def __str__(self):
        return f"Deal #{self.id} - {self.applicant.full_name} - {self.status}"

    @property
    def balance(self):
        """Calculate remaining balance."""
        return self.amount - self.paid_amount

    @property
    def is_paid(self):
        return self.payment_status == self.PAYMENT_PAID

    @property
    def deal_id(self):
        """Auto-generated deal ID."""
        return f"DL-{self.id:06d}"


class DealNote(models.Model):
    """Notes specific to a deal for tracking updates."""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="deal_notes")
    content = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="If true, only staff can see")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "deal_notes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on Deal {self.deal_id} by {self.author}"
