"""
User and Partner models. Partner approval status for registration flow.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user: can be Partner or Staff/Admin."""
    ROLE_PARTNER = "partner"
    ROLE_APPLICANT = "applicant"
    ROLE_STAFF = "staff"
    ROLE_ADMIN = "admin"
    ROLE_TEAM_MEMBER = "team_member"
    ROLE_CHOICES = [
        (ROLE_PARTNER, "Partner"),
        (ROLE_APPLICANT, "Applicant"),
        (ROLE_STAFF, "Staff"),
        (ROLE_ADMIN, "Admin"),
        (ROLE_TEAM_MEMBER, "Team Member"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_PARTNER)
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    @property
    def is_staff_or_admin(self):
        return self.role in (self.ROLE_STAFF, self.ROLE_ADMIN) or self.is_superuser

    @property
    def is_partner(self):
        return self.role == self.ROLE_PARTNER and not self.is_superuser


class Partner(models.Model):
    """Partner company: linked to User. Optional approval after registration."""
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_BLOCKED = "blocked"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_BLOCKED, "Blocked"),
    ]
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, related_name="partner")
    company_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    # Commission: admin sets per partner
    commission_type = models.CharField(
        max_length=20,
        choices=[("percent", "Percent"), ("fixed", "Fixed Amount")],
        default="percent",
    )
    commission_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Percentage (e.g. 10) or fixed amount per paid applicant",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "partners"
        ordering = ["-created_at"]

    def __str__(self):
        return self.company_name


class TeamInvitation(models.Model):
    """Invitation for team members to join the platform."""
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_EXPIRED, "Expired"),
    ]
    
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES, default=User.ROLE_TEAM_MEMBER)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_invitations")
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = "team_invitations"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Invitation to {self.email}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class EmailVerification(models.Model):
    """Email verification tokens for user registration."""
    STATUS_PENDING = "pending"
    STATUS_VERIFIED = "verified"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_VERIFIED, "Verified"),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="email_verification")
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = "email_verifications"
    
    def __str__(self):
        return f"Verification for {self.user.email}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class TwoFactorAuth(models.Model):
    """Two-Factor Authentication settings for users."""
    METHOD_CHOICES = [
        ("email", "Email"),
        ("totp", "Authenticator App"),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="two_factor_auth")
    is_enabled = models.BooleanField(default=False)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default="email")
    secret_key = models.CharField(max_length=32, blank=True)
    backup_codes = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "two_factor_auth"
    
    def __str__(self):
        return f"2FA for {self.user.email}"
