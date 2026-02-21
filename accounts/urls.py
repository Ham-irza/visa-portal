from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    PartnerRegisterView,
    ApplicantRegisterView,
    CustomTokenObtainPairView,
    MeView,
    PartnerListAdminView,
    PartnerDetailAdminView,
    PartnerApproveView,
    TeamMemberListView,
    TeamInvitationListCreateView,
    TeamInvitationDetailView,
    AcceptInvitationView,
    VerifyEmailView,
    ResendVerificationView,
    TwoFactorAuthView,
    TwoFactorAuthVerifyView,
    SendVerificationCodeView,
    ChangePasswordView,
    AddPartnerAsTeamMemberView,
)

urlpatterns = [
    path("register/", PartnerRegisterView.as_view(), name="register"),
    path("register/applicant/", ApplicantRegisterView.as_view(), name="register-applicant"),
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("partners/", PartnerListAdminView.as_view(), name="partner-list-admin"),
    path("partners/<int:pk>/", PartnerDetailAdminView.as_view(), name="partner-detail-admin"),
    path("partners/<int:pk>/approve/", PartnerApproveView.as_view(), name="partner-approve"),
    path("team/", TeamMemberListView.as_view(), name="team-list"),
    # Team Invitations
    path("team/invitations/", TeamInvitationListCreateView.as_view(), name="team-invitations"),
    path("team/invitations/<int:pk>/", TeamInvitationDetailView.as_view(), name="team-invitation-detail"),
    path("team/add-partner/", AddPartnerAsTeamMemberView.as_view(), name="add-partner-team-member"),
    path("accept-invitation/", AcceptInvitationView.as_view(), name="accept-invitation"),
    # Email Verification
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend-verification"),
    # Two-Factor Authentication
    path("two-factor-auth/", TwoFactorAuthView.as_view(), name="two-factor-auth"),
    path("two-factor-auth/verify/", TwoFactorAuthVerifyView.as_view(), name="two-factor-auth-verify"),
    path("two-factor-auth/send-code/", SendVerificationCodeView.as_view(), name="two-factor-auth-send-code"),
    # Password
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]
