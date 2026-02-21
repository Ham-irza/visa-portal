"""
Deals API Views with data isolation for partners.
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum

from .models import Deal, DealNote
from .serializers import (
    DealSerializer, DealListSerializer, 
    DealCreateSerializer, DealUpdateSerializer,
    DealNoteSerializer
)
from core.mixins import get_partner_for_request, filter_queryset_by_partner
from core.permissions import IsAdminOrStaff
from applicants.models import Applicant
from accounts.models import User


class DealViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Deals with data isolation:
    - Partners see only their own deals
    - Admins see all deals
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter deals based on user role."""
        user = self.request.user
        
        # Admins/Staff see all deals
        if getattr(user, "is_staff_or_admin", False):
            return Deal.objects.all().select_related(
                'applicant', 'partner', 'assigned_to'
            ).prefetch_related('notes')
        
        # Partners see only their own deals
        partner = get_partner_for_request(self.request)
        if partner:
            return Deal.objects.filter(partner=partner).select_related(
                'applicant', 'partner', 'assigned_to'
            ).prefetch_related('notes')
        
        # Fallback: return empty queryset
        return Deal.objects.none()
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'list':
            return DealListSerializer
        if self.action == 'create':
            return DealCreateSerializer
        if self.action in ['update', 'partial_update']:
            return DealUpdateSerializer
        return DealSerializer
    
    def get_partner_applicants(self):
        """Get applicants that belong to the current partner."""
        user = self.request.user
        if getattr(user, "is_staff_or_admin", False):
            return Applicant.objects.all()
        
        partner = get_partner_for_request(self.request)
        if partner:
            return Applicant.objects.filter(partner=partner)
        return Applicant.objects.none()
    
    def list(self, request, *args, **kwargs):
        """List deals with filtering support."""
        queryset = self.get_queryset()
        
        # Apply filters
        status_filter = request.query_params.get('status')
        payment_status_filter = request.query_params.get('payment_status')
        search = request.query_params.get('search')
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if payment_status_filter:
            queryset = queryset.filter(payment_status=payment_status_filter)
        
        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)
        
        if to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)
        
        if search:
            queryset = queryset.filter(
                Q(applicant__full_name__icontains=search) |
                Q(applicant__phone__icontains=search) |
                Q(applicant__email__icontains=search)
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create a new deal."""
        # Check if partner can create deal for this applicant
        applicant_id = request.data.get('applicant')
        if applicant_id:
            try:
                applicant = Applicant.objects.get(id=applicant_id)
                user = request.user
                
                # For partners, verify applicant belongs to them
                if not getattr(user, "is_staff_or_admin", False):
                    partner = get_partner_for_request(request)
                    if partner and applicant.partner != partner:
                        return Response(
                            {"detail": "You can only create deals for your own applicants."},
                            status=status.HTTP_403_FORBIDDEN
                        )
            except Applicant.DoesNotExist:
                pass
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update a deal with permission checks."""
        instance = self.get_object()
        user = request.user
        
        # Partners cannot change status/payment fields directly
        if not getattr(user, "is_staff_or_admin", False):
            restricted_fields = ['status', 'payment_status', 'paid_amount', 'assigned_to']
            for field in restricted_fields:
                if field in request.data:
                    return Response(
                        {field: "You don't have permission to modify this field."},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update with permission checks."""
        return self.update(request, *args, **kwargs)


class DealNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for Deal Notes."""
    permission_classes = [IsAuthenticated]
    serializer_class = DealNoteSerializer
    
    def get_queryset(self):
        """ notes based on user role and deal accessFilter."""
        user = self.request.user
        
        # Start with all notes
        queryset = DealNote.objects.all().select_related('author', 'deal')
        
        # If partner, only see their deal's partner notes
        if not getattr(user, "is_staff_or_admin", False):
            partner = get_partner_for_request(self.request)
            if partner:
                # Partners can see partner notes (is_internal=False) for their deals
                queryset = queryset.filter(
                    deal__partner=partner,
                    is_internal=False
                )
        
        # Filter by deal_id if provided
        deal_id = self.kwargs.get('deal_pk')
        if deal_id:
            queryset = queryset.filter(deal_id=deal_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set author on create."""
        serializer.save(author=self.request.user)


class DealStatsViewSet(viewsets.ViewSet):
    """Get deal statistics for the current user."""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get deal statistics."""
        user = request.user
        
        # Get base queryset
        if getattr(user, "is_staff_or_admin", False):
            deals = Deal.objects.all()
        else:
            partner = get_partner_for_request(request)
            if partner:
                deals = Deal.objects.filter(partner=partner)
            else:
                deals = Deal.objects.none()
        
        # Calculate stats
        total_deals = deals.count()
        total_amount = deals.aggregate(sum=Sum('amount'))['sum'] or 0
        total_paid = deals.aggregate(sum=Sum('paid_amount'))['sum'] or 0
        total_balance = total_amount - total_paid
        
        # By status
        by_status = {}
        for status_choice in Deal.STATUS_CHOICES:
            status_value = status_choice[0]
            count = deals.filter(status=status_value).count()
            by_status[status_value] = count
        
        # By payment status
        by_payment_status = {}
        for payment_status_choice in Deal.PAYMENT_STATUS_CHOICES:
            status_value = payment_status_choice[0]
            count = deals.filter(payment_status=status_value).count()
            by_payment_status[status_value] = count
        
        return Response({
            'total_deals': total_deals,
            'total_amount': float(total_amount),
            'total_paid': float(total_paid),
            'total_balance': float(total_balance),
            'by_status': by_status,
            'by_payment_status': by_payment_status,
        })
