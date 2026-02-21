from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import Partner, TeamInvitation, EmailVerification, TwoFactorAuth

User = get_user_model()

class PartnerSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for Partner profile data.
    """
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Partner
        fields = [
            "id",
            "email",
            "company_name",
            "contact_name",
            "contact_phone",
            "status",
            "commission_type",
            "commission_rate",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PartnerRegisterSerializer(serializers.Serializer):
    """
    Handles registration for Partners.
    Automatically sets username=email to satisfy DB requirements.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    company_name = serializers.CharField(max_length=255)
    contact_name = serializers.CharField(max_length=255)
    contact_phone = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        # 1. Create the User instance with is_active=False (requires email verification)
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['email'],  # Copy email to username to satisfy DB constraint
            password=validated_data['password'],
            role=User.ROLE_PARTNER,
            is_active=False  # User must verify email before logging in
        )

        # 2. Create the Partner profile linked to the user
        partner = Partner.objects.create(
            user=user,
            company_name=validated_data['company_name'],
            contact_name=validated_data['contact_name'],
            contact_phone=validated_data.get('contact_phone', '')
        )
        
        return partner


class ApplicantRegisterSerializer(serializers.Serializer):
    """
    Handles registration for Applicants (Regular Users).
    Automatically sets username=email to satisfy DB requirements.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=255, required=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        # 1. Create the User instance with is_active=False (requires email verification)
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['email'],  # Copy email to username
            password=validated_data['password'],
            role=User.ROLE_APPLICANT,
            is_active=False  # User must verify email before logging in
        )
        
        # 2. Set extra fields if provided
        if 'full_name' in validated_data:
            # Assuming you want to split full_name or store it in first_name
            user.first_name = validated_data['full_name']
            user.save()
            
        return user


class UserMeSerializer(serializers.ModelSerializer):
    """
    Serializer for the /me/ endpoint to return current user info.
    """
    partner = PartnerSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "role",
            "partner",
        ]


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Serializer.
    Because User.USERNAME_FIELD is 'email', this naturally accepts 'email' & 'password'.
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims to the token payload
        token["email"] = user.email
        token["role"] = user.role
        token["is_partner"] = user.is_partner
        
        # Add partner status if applicable
        if user.is_partner and hasattr(user, 'partner'):
            token["partner_status"] = user.partner.status
            
        return token


class TeamInvitationSerializer(serializers.ModelSerializer):
    """Serializer for team invitations."""
    
    class Meta:
        model = TeamInvitation
        fields = [
            "id",
            "email",
            "role",
            "status",
            "created_at",
            "expires_at",
        ]
        read_only_fields = ["id", "status", "created_at", "expires_at"]


class EmailVerificationSerializer(serializers.ModelSerializer):
    """Serializer for email verification."""
    
    class Meta:
        model = EmailVerification
        fields = [
            "id",
            "user",
            "token",
            "status",
            "created_at",
            "expires_at",
        ]
        read_only_fields = ["id", "token", "status", "created_at", "expires_at"]


class TwoFactorAuthSerializer(serializers.ModelSerializer):
    """Serializer for Two-Factor Authentication."""
    
    class Meta:
        model = TwoFactorAuth
        fields = [
            "id",
            "is_enabled",
            "method",
            "backup_codes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "backup_codes", "created_at", "updated_at"]
    
    def to_representation(self, instance):
        # Don't expose backup codes in regular responses
        data = super().to_representation(instance)
        if instance.backup_codes:
            data['backup_codes'] = f"{len(instance.backup_codes)} codes remaining"
        return data
