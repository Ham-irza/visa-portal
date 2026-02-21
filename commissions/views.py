from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from .models import Commission, CommissionRule
from .serializers import CommissionSerializer, CommissionListSerializer, CommissionRuleSerializer
from core.mixins import filter_queryset_by_partner
from core.permissions import PartnerDataIsolation


class CommissionRuleViewSet(viewsets.ModelViewSet):
    """
    Endpoints for Commission Rules (Tiers, Rates).
    - READ: Available to all authenticated users (for frontend calculator).
    - WRITE: Restricted to Admins only.
    """
    queryset = CommissionRule.objects.all()
    serializer_class = CommissionRuleSerializer
    pagination_class = None  # Return all rules in one response for the UI

    def get_permissions(self):
        """
        Custom permissions:
        - Lists/Retreives are allowed for any logged-in user.
        - Creates/Updates/Deletes require Admin status.
        """
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]


class CommissionViewSet(viewsets.ModelViewSet):
    """
    Commission endpoints:
    - Partners: Can only READ (list/retrieve) their own commissions.
    - Admins/Staff: Can READ all, and CREATE/UPDATE/DELETE.
    """
    permission_classes = [PartnerDataIsolation]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["applicant", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Commission.objects.all().select_related("applicant", "applicant__partner")
        return filter_queryset_by_partner(qs, self.request, "applicant__partner")

    def get_serializer_class(self):
        if self.action == "list":
            return CommissionListSerializer
        return CommissionSerializer

    # --- Write Protections (Staff/Admin Only) ---

    def create(self, request, *args, **kwargs):
        if not self._is_staff_or_admin(request.user):
            return Response({"detail": "Only staff can create commissions."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not self._is_staff_or_admin(request.user):
            return Response({"detail": "Only staff can update commissions."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self._is_staff_or_admin(request.user):
            return Response({"detail": "Only staff can update commissions."}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._is_staff_or_admin(request.user):
            return Response({"detail": "Only staff can delete commissions."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def _is_staff_or_admin(self, user):
        """Helper to check write permissions"""
        return getattr(user, "is_staff_or_admin", False) or user.is_staff or user.is_superuser