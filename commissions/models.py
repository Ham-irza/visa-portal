"""
Commission per applicant (when paid). 
Partner rate set on Partner; Commission records per applicant.
Includes Commission Rules for tier-based calculations.
"""
from django.db import models
from applicants.models import Applicant

# --- 1. The Commission Record (Earnings) ---
class Commission(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_PROCESSING = "processing" # Added to match frontend 'processing' state if needed
    
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_PAID, "Paid"),
    ]

    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name="commissions",
        null=False,
        blank=False,
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    # Payment Tracking
    paid_at = models.DateTimeField(null=True, blank=True)
    payout_reference = models.CharField(max_length=100, blank=True, help_text="Transaction ID or Check #")
    notes = models.TextField(blank=True)
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commissions"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["applicant"])]

    def __str__(self):
        return f"{self.amount} {self.currency} - {self.applicant.full_name}"


# --- 2. The Commission Rules (Tiers & Logic) ---
class CommissionRule(models.Model):
    """
    Defines the logic for commission calculation (e.g. Silver Tier = 7%).
    This solves the 'public.commission_rules' missing table error.
    """
    TIER_BRONZE = 'Bronze'
    TIER_SILVER = 'Silver'
    TIER_GOLD = 'Gold'
    TIER_PLATINUM = 'Platinum'

    TIER_CHOICES = [
        (TIER_BRONZE, 'Bronze'),
        (TIER_SILVER, 'Silver'),
        (TIER_GOLD, 'Gold'),
        (TIER_PLATINUM, 'Platinum'),
    ]

    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    
    # Calculation Factors
    base_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        help_text="Base percentage (e.g., 5.00 for 5%)"
    )
    bonus_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00, 
        help_text="Extra percentage if threshold is met"
    )
    threshold = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        help_text="Deal value amount required to trigger the bonus"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commission_rules" # Matches the error expectation
        ordering = ["base_rate"]
        verbose_name = "Commission Rule"
        verbose_name_plural = "Commission Rules"

    def __str__(self):
        return f"{self.tier} - Base: {self.base_rate}%"