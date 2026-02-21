from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from datetime import timedelta
import logging

from .models import Partner, TeamInvitation, EmailVerification, TwoFactorAuth
from .serializers import (
    PartnerRegisterSerializer,
    PartnerSerializer,
    UserMeSerializer,
    ApplicantRegisterSerializer,
    TeamInvitationSerializer,
    EmailVerificationSerializer,
    TwoFactorAuthSerializer,
)
from core.permissions import IsAdminOrStaff

User = get_user_model()
logger = logging.getLogger(__name__)


class PartnerRegisterView(generics.CreateAPIView):
    """Partner registration. Creates User + Partner (status=pending)."""
    permission_classes = [AllowAny]
    serializer_class = PartnerRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        partner = serializer.save()
        
        # Send verification email
        user = partner.user
        token = get_random_string(64)
        expires_at = timezone.now() + timedelta(days=7)
        
        # Create verification token
        verification, created = EmailVerification.objects.update_or_create(
            user=user,
            defaults={
                'token': token,
                'status': EmailVerification.STATUS_PENDING,
                'expires_at': expires_at
            }
        )
        
        # Send verification email
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        verification_link = f"{frontend_url}/verify-email?token={token}"
        
        logger.error(f"EMAIL DEBUG - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}, User: {settings.EMAIL_HOST_USER}, From: {settings.DEFAULT_FROM_EMAIL}")
        
        try:
            result = send_mail(
                subject="Verify your Hainan Builder Portal account",
                message=f"Welcome! Please verify your email address by clicking the link below:\n\n{verification_link}\n\nThis link expires in 7 days.\n\nAfter verification, your account will be active.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.error(f"EMAIL DEBUG - send_mail result: {result}")
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            import traceback
            logger.error(f"Email error traceback: {traceback.format_exc()}")
        
        return Response(
            {"detail": "Registration successful. Please check your email to verify your account."},
            status=status.HTTP_201_CREATED,
        )


class ApplicantRegisterView(generics.CreateAPIView):
    """Applicant self-registration: creates a plain User (no Partner)."""
    permission_classes = [AllowAny]
    serializer_class = ApplicantRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email
        token = get_random_string(64)
        expires_at = timezone.now() + timedelta(days=7)
        
        # Create verification token
        verification, created = EmailVerification.objects.update_or_create(
            user=user,
            defaults={
                'token': token,
                'status': EmailVerification.STATUS_PENDING,
                'expires_at': expires_at
            }
        )
        
        # Send verification email
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        verification_link = f"{frontend_url}/verify-email?token={token}"
        
        try:
            send_mail(
                subject="Verify your Hainan Builder Portal account",
                message=f"Welcome! Please verify your email address by clicking the link below:\n\n{verification_link}\n\nThis link expires in 7 days.\n\nAfter verification, your account will be active.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
        
        return Response(
            {"detail": "Registration successful. Please check your email to verify your account."},
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT login. Only allows login for users with is_active=True."""

    def post(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"LOGIN DEBUG - request.data: {request.data}")
        
        # First, check if user exists and is_active before attempting JWT login
        username_or_email = request.data.get("username") or request.data.get("email")
        user = User.objects.filter(username=username_or_email).first()
        if not user:
            user = User.objects.filter(email=username_or_email).first()
        
        logger.error(f"LOGIN DEBUG - found user: {user}, is_active: {user.is_active if user else 'N/A'}")
        
        # Check if account is active
        if user and not user.is_active:
            return Response(
                {"detail": "Your account is not active. Please verify your email first."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        # Check if partner is blocked
        if user and user.is_partner:
            try:
                partner = user.partner
                if partner.status == Partner.STATUS_BLOCKED:
                    return Response(
                        {"detail": "Your account has been blocked."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            except Partner.DoesNotExist:
                pass
        
        response = super().post(request, *args, **kwargs)
        logger.error(f"LOGIN DEBUG - response.status: {response.status_code}")
        
        if response.status_code != 200:
            return response
            
        return response


class MeView(generics.RetrieveAPIView):
    """Current user + partner info."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserMeSerializer

    def get_object(self):
        return self.request.user


class PartnerListAdminView(generics.ListAPIView):
    """Admin: list all partners."""
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    serializer_class = PartnerSerializer
    queryset = Partner.objects.all().select_related("user")
    filterset_fields = ["status"]


class PartnerDetailAdminView(generics.RetrieveUpdateAPIView):
    """Admin: retrieve/update partner (approve, block, edit)."""
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    serializer_class = PartnerSerializer
    queryset = Partner.objects.all().select_related("user")


class PartnerApproveView(APIView):
    """Admin: approve a pending partner (change status to approved)."""
    permission_classes = [IsAuthenticated, IsAdminOrStaff]

    def post(self, request, pk):
        try:
            partner = Partner.objects.get(pk=pk)
        except Partner.DoesNotExist:
            return Response(
                {"detail": "Partner not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if partner.status != Partner.STATUS_PENDING:
            return Response(
                {"detail": f"Only pending partners can be approved. Current status: {partner.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        partner.status = Partner.STATUS_APPROVED
        partner.save()

        return Response(
            {
                "detail": "Partner approved successfully.",
                "partner": PartnerSerializer(partner).data,
            },
            status=status.HTTP_200_OK,
        )


class TeamMemberListView(generics.ListAPIView):
    """Admin: list all team members (staff/admin users)."""
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    serializer_class = None  # Will be defined below
    
    def get_serializer_class(self):
        from .serializers import UserMeSerializer
        return UserMeSerializer

    def get_queryset(self):
        return User.objects.filter(
            role__in=[User.ROLE_STAFF, User.ROLE_ADMIN, User.ROLE_TEAM_MEMBER]
        ).select_related('partner')


class TeamInvitationListCreateView(generics.ListCreateAPIView):
    """Admin: list and create team invitations."""
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    serializer_class = TeamInvitationSerializer
    
    def get_queryset(self):
        return TeamInvitation.objects.filter(invited_by=self.request.user)
    
    def perform_create(self, serializer):
        email = serializer.validated_data['email']
        role = serializer.validated_data.get('role', User.ROLE_TEAM_MEMBER)
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        
        # Generate token
        token = get_random_string(64)
        expires_at = timezone.now() + timedelta(days=7)
        
        invitation = serializer.save(
            invited_by=self.request.user,
            token=token,
            expires_at=expires_at
        )
        
        # Send invitation email
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        invitation_link = f"{frontend_url}/accept-invitation?token={token}"
        
        try:
            send_mail(
                subject="You're invited to join the Hainan Builder Portal",
                message=f"You have been invited to join the Hainan Builder Portal as a {role}.\n\nClick the link below to accept the invitation:\n\n{invitation_link}\n\nThis invitation expires in 7 days.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send invitation email: {e}")


class TeamInvitationDetailView(generics.RetrieveDestroyAPIView):
    """Admin: retrieve or delete a team invitation."""
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    serializer_class = TeamInvitationSerializer
    
    def get_queryset(self):
        return TeamInvitation.objects.filter(invited_by=self.request.user)


class AcceptInvitationView(APIView):
    """Accept a team invitation and create account."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')
        full_name = request.data.get('full_name', '')
        
        if not token or not password:
            return Response(
                {"detail": "Token and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            invitation = TeamInvitation.objects.get(token=token)
        except TeamInvitation.DoesNotExist:
            return Response(
                {"detail": "Invalid invitation token."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if invitation.status != TeamInvitation.STATUS_PENDING:
            return Response(
                {"detail": "This invitation has already been used or expired."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.is_expired():
            invitation.status = TeamInvitation.STATUS_EXPIRED
            invitation.save()
            return Response(
                {"detail": "This invitation has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user account
        email = invitation.email
        username = email  # Use email as username
        
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            role=invitation.role,
            first_name=full_name.split()[0] if full_name else '',
            last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
        )
        
        # Update invitation status
        invitation.status = TeamInvitation.STATUS_ACCEPTED
        invitation.save()
        
        return Response(
            {"detail": "Account created successfully. You can now login."},
            status=status.HTTP_201_CREATED
        )


class VerifyEmailView(APIView):
    """Verify email address using token."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response(
                {"detail": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            verification = EmailVerification.objects.get(token=token)
        except EmailVerification.DoesNotExist:
            return Response(
                {"detail": "Invalid verification token."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if verification.status == EmailVerification.STATUS_VERIFIED:
            return Response(
                {"detail": "Email already verified."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if verification.is_expired():
            return Response(
                {"detail": "Verification token has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the user and activate their account
        user = verification.user
        
        # Activate the user account
        user.is_active = True
        user.save()
        
        # If user is a partner, auto-approve them
        if user.is_partner and hasattr(user, 'partner'):
            user.partner.status = Partner.STATUS_APPROVED
            user.partner.save()
        
        # Mark email as verified
        verification.status = EmailVerification.STATUS_VERIFIED
        verification.save()
        
        return Response(
            {"detail": "Email verified successfully. Your account is now active."},
            status=status.HTTP_200_OK
        )


class ResendVerificationView(APIView):
    """Resend verification email."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if user exists
            return Response(
                {"detail": "If the email exists, a verification link has been sent."},
                status=status.HTTP_200_OK
            )
        
        # Check if already verified
        if hasattr(user, 'email_verification') and user.email_verification.status == EmailVerification.STATUS_VERIFIED:
            return Response(
                {"detail": "Email already verified."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update verification token
        token = get_random_string(64)
        expires_at = timezone.now() + timedelta(days=7)
        
        verification, created = EmailVerification.objects.update_or_create(
            user=user,
            defaults={
                'token': token,
                'status': EmailVerification.STATUS_PENDING,
                'expires_at': expires_at
            }
        )
        
        # Send verification email
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        verification_link = f"{frontend_url}/verify-email?token={token}"
        
        try:
            send_mail(
                subject="Verify your Hainan Builder Portal account",
                message=f"Please verify your email address by clicking the link below:\n\n{verification_link}\n\nThis link expires in 7 days.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
        
        return Response(
            {"detail": "If the email exists, a verification link has been sent."},
            status=status.HTTP_200_OK
        )


class TwoFactorAuthView(generics.RetrieveUpdateAPIView):
    """Get or update 2FA settings."""
    permission_classes = [IsAuthenticated]
    serializer_class = TwoFactorAuthSerializer
    
    def get_object(self):
        two_fa, created = TwoFactorAuth.objects.get_or_create(user=self.request.user)
        return two_fa
    
    def perform_update(self, serializer):
        # If enabling 2FA, generate secret key
        if serializer.validated_data.get('is_enabled') and not serializer.instance.is_enabled:
            import secrets
            serializer.instance.secret_key = secrets.token_hex(16)
            # Generate backup codes
            serializer.instance.backup_codes = [secrets.token_hex(4) for _ in range(10)]
        serializer.save()


class TwoFactorAuthVerifyView(APIView):
    """Verify 2FA code."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response(
                {"detail": "Code is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            two_fa = TwoFactorAuth.objects.get(user=request.user)
        except TwoFactorAuth.DoesNotExist:
            return Response(
                {"detail": "2FA is not enabled for this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not two_fa.is_enabled:
            return Response(
                {"detail": "2FA is not enabled."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check backup code first
        if code in two_fa.backup_codes:
            # Remove used backup code
            codes = two_fa.backup_codes
            codes.remove(code)
            two_fa.backup_codes = codes
            two_fa.save()
            return Response(
                {"detail": "Verification successful.", "backup_code_used": True},
                status=status.HTTP_200_OK
            )
        
        # For email method, send verification code
        if two_fa.method == "email":
            # Generate and send code
            import secrets
            verification_code = secrets.token_hex(3).upper()
            
            # Store code temporarily (in production, use cache with expiry)
            request.session['2fa_code'] = verification_code
            request.session['2fa_code_expires'] = str(timezone.now() + timedelta(minutes=5))
            
            try:
                send_mail(
                    subject="Your Hainan Builder Portal verification code",
                    message=f"Your verification code is: {verification_code}\n\nThis code expires in 5 minutes.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Failed to send 2FA email: {e}")
            
            return Response(
                {"detail": "Verification code sent to your email."},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"detail": "Invalid verification code."},
            status=status.HTTP_400_BAD_REQUEST
        )


class SendVerificationCodeView(APIView):
    """Send 2FA verification code to email."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            two_fa = TwoFactorAuth.objects.get(user=request.user)
        except TwoFactorAuth.DoesNotExist:
            return Response(
                {"detail": "2FA is not enabled."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not two_fa.is_enabled or two_fa.method != "email":
            return Response(
                {"detail": "Email 2FA is not enabled."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate and send code
        import secrets
        verification_code = secrets.token_hex(3).upper()
        
        request.session['2fa_code'] = verification_code
        request.session['2fa_code_expires'] = str(timezone.now() + timedelta(minutes=5))
        
        try:
            send_mail(
                subject="Your Hainan Builder Portal verification code",
                message=f"Your verification code is: {verification_code}\n\nThis code expires in 5 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send 2FA email: {e}")
            return Response(
                {"detail": "Failed to send verification code."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            {"detail": "Verification code sent."},
            status=status.HTTP_200_OK
        )


class ChangePasswordView(APIView):
    """Change user password."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from django.contrib.auth import authenticate
        
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            return Response(
                {"detail": "All password fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != confirm_password:
            return Response(
                {"detail": "New passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 8:
            return Response(
                {"detail": "Password must be at least 8 characters."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        # Verify current password
        if not user.check_password(current_password):
            return Response(
                {"detail": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK
        )


class AddPartnerAsTeamMemberView(APIView):
    """Add an existing partner as a team member."""
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    
    def post(self, request):
        partner_id = request.data.get('partner_id')
        role = request.data.get('role', 'team_member')
        
        if not partner_id:
            return Response(
                {"detail": "partner_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            partner = Partner.objects.get(pk=partner_id)
        except Partner.DoesNotExist:
            return Response(
                {"detail": "Partner not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user = partner.user
        
        # Update user role
        user.role = role
        user.save()
        
        return Response(
            {
                "detail": f"Partner {partner.company_name} added as {role}",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                }
            },
            status=status.HTTP_200_OK
        )


# Import serializers at the end to avoid circular imports
from rest_framework import serializers
