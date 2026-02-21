"""
Support tickets: partner opens ticket; admin/staff replies.
"""
from django.db import models
from django.conf import settings
from accounts.models import Partner


class Ticket(models.Model):
    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_CLOSED, "Closed"),
    ]
    
    CATEGORY_GENERAL = "general"
    CATEGORY_TECHNICAL = "technical"
    CATEGORY_BILLING = "billing"
    CATEGORY_REFERRAL = "referral"
    CATEGORY_COMMISSION = "commission"
    CATEGORY_ACCOUNT = "account"
    CATEGORY_CHOICES = [
        (CATEGORY_GENERAL, "General"),
        (CATEGORY_TECHNICAL, "Technical"),
        (CATEGORY_BILLING, "Billing"),
        (CATEGORY_REFERRAL, "Referral"),
        (CATEGORY_COMMISSION, "Commission"),
        (CATEGORY_ACCOUNT, "Account"),
    ]
    
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    ]
    
    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="tickets",
        null=False,
        blank=False,
    )
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_GENERAL)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tickets"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["partner", "status"])]

    def __str__(self):
        return f"#{self.id} {self.subject}"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="messages",
        null=False,
        blank=False,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ticket_messages",
        null=False,
        blank=False,
    )
    body = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ticket_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"Message on #{self.ticket_id} by {self.author_id}"
