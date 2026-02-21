import logging
from rest_framework import viewsets, filters, status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import IsAuthenticated 
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ObjectDoesNotExist

from .models import Applicant
from .serializers import ApplicantSerializer, ApplicantListSerializer
# If you have your custom permission, you can use it, otherwise IsAuthenticated is safe
from core.permissions import IsPartnerOwnerOrAdmin 

# Set up logging to help debug if something goes wrong
logger = logging.getLogger(__name__)

class ApplicantViewSet(viewsets.ModelViewSet):
    """
    Applicants API:
    - Partners see ONLY their own applicants.
    - Admins see ALL applicants.
    - Supports searching by Name, Passport, Email.
    """
    # Use IsAuthenticated so even standard users can hit the endpoint (logic inside handles scope)
    permission_classes = [IsAuthenticated] 
    
    # Enable robust filtering and searching
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Exact match filters (e.g. ?status=approved)
    filterset_fields = ["status", "visa_type", "destination_country", "gender"]
    
    # Fuzzy search (e.g. ?search=AB123456)
    search_fields = ["full_name", "email", "passport_number", "phone"]
    
    # Sorting
    ordering_fields = ["created_at", "full_name", "status", "travel_date"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        # Use the lighter serializer for lists (faster), full serializer for details
        if self.action == "list":
            return ApplicantListSerializer
        return ApplicantSerializer

    def get_queryset(self):
        """
        Security Filter:
        - Admin: Returns all.
        - Partner: Returns ONLY their own data.
        """
        user = self.request.user
        qs = Applicant.objects.select_related("partner").all()

        # 1. Admin / Staff see everything
        if user.is_staff or user.is_superuser or getattr(user, 'role', '') in ['ADMIN', 'STAFF']:
            return qs
        
        # 2. Partners see only their own
        # We check both possible related_names to be safe
        if hasattr(user, 'partner') and getattr(user, 'partner', None):
            return qs.filter(partner=user.partner)
        if hasattr(user, 'partner_profile') and getattr(user, 'partner_profile', None):
            return qs.filter(partner=user.partner_profile)

        # 3. Individual applicants (logged-in users who registered themselves)
        # Return only the applicant records owned by this user.
        try:
            if Applicant.objects.filter(applicant_user=user).exists():
                return qs.filter(applicant_user=user)
        except Exception:
            # If Applicant table inaccessible for some reason, fall through
            pass

        # 4. Fallback: standard users see nothing
        return Applicant.objects.none()

    def perform_create(self, serializer):
        """
        Auto-assign the correct partner to the applicant.
        """
        user = self.request.user
        print(f"DEBUG: perform_create for User: {user.email} (ID: {user.id})")

        # 1. Try to find the Partner Profile linked to this user
        partner_obj = None
        try:
            if hasattr(user, 'partner') and user.partner:
                partner_obj = user.partner
            elif hasattr(user, 'partner_profile') and user.partner_profile:
                partner_obj = user.partner_profile
        except ObjectDoesNotExist:
            partner_obj = None

        # 2. LOGIC: Assign Partner
        if partner_obj:
            # ✅ SUCCESS: User is a normal Partner
            print(f"DEBUG: Found Partner Profile ID: {partner_obj.id}")
            serializer.save(partner=partner_obj)

        elif user.is_staff or user.is_superuser:
            # ⚠️ ADMIN CASE: Admins can create applicants with or without a partner.
            # If partner ID is provided, use it. Otherwise, create without partner association.
            partner_id = self.request.data.get('partner')
            if partner_id:
                print(f"DEBUG: Admin manually assigned Partner ID: {partner_id}")
                serializer.save(partner_id=partner_id)
            else:
                # Admin can create applicant without partner association
                print(f"DEBUG: Admin creating applicant without partner association")
                serializer.save()
        else:
            # Standard authenticated user creating their own applicant profile.
            # If the user has role 'applicant', ensure they cannot set a partner
            # or create applications on behalf of others.
            user_role = getattr(user, 'role', '').lower()
            if user_role == 'applicant':
                # Reject if payload attempts to set partner or applicant_user
                if self.request.data.get('partner') or self.request.data.get('applicant_user'):
                    raise PermissionDenied("Applicant users may only create applications for themselves.")
                # Ensure the created Applicant is linked to this user
                serializer.save(applicant_user=user)
                return

            # Non-applicant standard authenticated users (e.g., partners without profile)
            # Save as applicant_user by default to avoid accidental partner ownership.
            serializer.save(applicant_user=user)