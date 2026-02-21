"""
Signals for handling user deletion cleanup.
"""
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(pre_delete, sender=User)
def cleanup_user_related_data_before_delete(sender, instance, **kwargs):
    """
    Delete all related data before user is deleted.
    This prevents foreign key constraint errors.
    """
    from .models import Partner, EmailVerification, TwoFactorAuth, TeamInvitation
    
    # Delete EmailVerification
    EmailVerification.objects.filter(user=instance).delete()
    
    # Delete TwoFactorAuth
    TwoFactorAuth.objects.filter(user=instance).delete()
    
    # Delete sent TeamInvitations
    TeamInvitation.objects.filter(invited_by=instance).delete()
    
    # Delete Partner (will set user to null via SET_NULL)
    Partner.objects.filter(user=instance).delete()
