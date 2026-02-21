"""
Payments per applicant. Amount, currency, status, invoice/receipt.
"""
from django.db import models
from applicants.models import Applicant


class Payment(models.Model):
    STATUS_UNPAID = "unpaid"
    STATUS_PAID = "paid"
    STATUS_PARTIAL = "partial"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = [
        (STATUS_UNPAID, "Unpaid"),
        (STATUS_PAID, "Paid"),
        (STATUS_PARTIAL, "Partial"),
        (STATUS_REFUNDED, "Refunded"),
    ]
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name="payments",
        null=False,
        blank=False,
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNPAID)
    payment_date = models.DateField(null=True, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    receipt_file = models.FileField(upload_to="receipts/%Y/%m/", blank=True, null=True, max_length=500)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["applicant", "status"])]

    def __str__(self):
        return f"{self.amount} {self.currency} - {self.applicant.full_name}"
