"""
Dashboard stats: total applicants, by status, pending docs, payments, commission.
Partner sees own; admin can pass ?partner_id= for a specific partner or see totals.
"""
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from applicants.models import Applicant
from accounts.models import Partner
from documents.models import Document
from payments.models import Payment
from commissions.models import Commission
from core.mixins import get_partner_for_request
from core.permissions import IsAdminOrStaff


class DashboardStatsView(APIView):
    """GET: dashboard stats (applicants, docs, payments, commission)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = get_partner_for_request(request)
        partner_id = request.query_params.get("partner_id")
        if getattr(request.user, "is_staff_or_admin", False) and partner_id:
            try:
                partner = Partner.objects.get(pk=int(partner_id))
            except (Partner.DoesNotExist, ValueError):
                partner = None
        if partner is None and not getattr(request.user, "is_staff_or_admin", False):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        applicant_qs = Applicant.objects.filter(partner=partner) if partner else Applicant.objects.all()
        total_applicants = applicant_qs.count()
        active = applicant_qs.filter(
            status__in=[Applicant.STATUS_NEW, Applicant.STATUS_DOCS_PENDING, Applicant.STATUS_PROCESSING]
        ).count()
        completed = applicant_qs.filter(
            status__in=[Applicant.STATUS_APPROVED, Applicant.STATUS_COMPLETED]
        ).count()
        rejected = applicant_qs.filter(status=Applicant.STATUS_REJECTED).count()

        doc_qs = Document.objects.filter(applicant__partner=partner) if partner else Document.objects.all()
        pending_docs = doc_qs.filter(status=Document.STATUS_PENDING).count()

        pay_qs = Payment.objects.filter(applicant__partner=partner) if partner else Payment.objects.all()
        paid_count = pay_qs.filter(status=Payment.STATUS_PAID).count()
        unpaid_count = pay_qs.filter(status=Payment.STATUS_UNPAID).count()
        total_revenue = sum(p.amount for p in pay_qs.filter(status=Payment.STATUS_PAID))

        comm_qs = Commission.objects.filter(applicant__partner=partner) if partner else Commission.objects.all()
        total_commission_earned = sum(c.amount for c in comm_qs)
        pending_commission = sum(c.amount for c in comm_qs.filter(status=Commission.STATUS_PENDING))
        paid_commission = sum(c.amount for c in comm_qs.filter(status=Commission.STATUS_PAID))

        return Response({
            "total_applicants": total_applicants,
            "active_applicants": active,
            "completed_applicants": completed,
            "rejected_applicants": rejected,
            "pending_documents": pending_docs,
            "paid_payments_count": paid_count,
            "unpaid_payments_count": unpaid_count,
            "total_revenue": total_revenue,
            "total_commission_earned": total_commission_earned,
            "commission_pending": pending_commission,
            "commission_paid": paid_commission,
        })


class AdminStatsView(APIView):
    """GET: admin dashboard stats - totals across all partners."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not getattr(request.user, "is_staff_or_admin", False):
            return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)

        # Get all stats across all partners
        total_applicants = Applicant.objects.count()
        active = Applicant.objects.filter(
            status__in=[Applicant.STATUS_NEW, Applicant.STATUS_DOCS_PENDING, Applicant.STATUS_PROCESSING]
        ).count()
        completed = Applicant.objects.filter(
            status__in=[Applicant.STATUS_APPROVED, Applicant.STATUS_COMPLETED]
        ).count()
        rejected = Applicant.objects.filter(status=Applicant.STATUS_REJECTED).count()
        pending_docs = Document.objects.filter(status=Document.STATUS_PENDING).count()
        
        total_partners = Partner.objects.count()
        approved_partners = Partner.objects.filter(status=Partner.STATUS_APPROVED).count()
        pending_partners = Partner.objects.filter(status=Partner.STATUS_PENDING).count()
        
        paid_payments_count = Payment.objects.filter(status=Payment.STATUS_PAID).count()
        unpaid_payments_count = Payment.objects.filter(status=Payment.STATUS_UNPAID).count()
        total_revenue = sum(p.amount for p in Payment.objects.filter(status=Payment.STATUS_PAID))
        
        total_commission_earned = sum(c.amount for c in Commission.objects.all())
        paid_commission = sum(c.amount for c in Commission.objects.filter(status=Commission.STATUS_PAID))
        
        return Response({
            "total_applicants": total_applicants,
            "active_applicants": active,
            "completed_applicants": completed,
            "rejected_applicants": rejected,
            "pending_documents": pending_docs,
            "total_partners": total_partners,
            "approved_partners": approved_partners,
            "pending_partners": pending_partners,
            "paid_payments_count": paid_payments_count,
            "unpaid_payments_count": unpaid_payments_count,
            "total_revenue": total_revenue,
            "total_commission_earned": total_commission_earned,
            "commission_paid": paid_commission,
        })
