"""
Reports: partner (own stats) and admin (all partners, rankings). Export CSV/PDF.
Now includes Deal-specific metrics.
"""
import csv
from datetime import datetime
from decimal import Decimal
from django.http import HttpResponse
from django.db.models import Count, Sum
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

from applicants.models import Applicant
from accounts.models import Partner
from payments.models import Payment
from commissions.models import Commission
from deals.models import Deal
from core.mixins import get_partner_for_request
from core.permissions import IsAdminOrStaff


class PartnerReportView(APIView):
    """Partner: report for own data (date range). GET with from_date, to_date."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = get_partner_for_request(request)
        if partner is None:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        
        # Applicant stats
        applicant_qs = Applicant.objects.filter(partner=partner)
        if from_date:
            applicant_qs = applicant_qs.filter(created_at__date__gte=from_date)
        if to_date:
            applicant_qs = applicant_qs.filter(created_at__date__lte=to_date)
        
        # Deal stats
        deal_qs = Deal.objects.filter(partner=partner)
        if from_date:
            deal_qs = deal_qs.filter(created_at__date__gte=from_date)
        if to_date:
            deal_qs = deal_qs.filter(created_at__date__lte=to_date)
        
        # Calculate stats
        total_applicants = applicant_qs.count()
        total_deals = deal_qs.count()
        
        # Payment stats
        paid_payments = Payment.objects.filter(
            applicant__partner=partner,
            status=Payment.STATUS_PAID,
            applicant__in=applicant_qs,
        )
        total_paid_amount = paid_payments.aggregate(s=Sum("amount"))["s"] or Decimal("0")
        
        # Deal payment stats
        deal_paid = deal_qs.aggregate(s=Sum("paid_amount"))["s"] or Decimal("0")
        
        # Commission
        commission = Commission.objects.filter(
            applicant__partner=partner,
            applicant__in=applicant_qs,
        ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        
        # Deal status breakdown
        deal_status = {}
        for status_choice in Deal.STATUS_CHOICES:
            status_value = status_choice[0]
            count = deal_qs.filter(status=status_value).count()
            deal_status[status_value] = count
        
        # Payment status breakdown
        payment_status = {}
        for pay_choice in Deal.PAYMENT_STATUS_CHOICES:
            status_value = pay_choice[0]
            count = deal_qs.filter(payment_status=status_value).count()
            payment_status[status_value] = count
        
        return Response({
            "from_date": from_date,
            "to_date": to_date,
            # Applicant stats
            "total_applicants_submitted": total_applicants,
            # Deal stats
            "total_deals": total_deals,
            "total_paid_amount": float(total_paid_amount),
            "total_commission_earned": float(commission),
            # Deal-specific financial
            "deal_total_amount": float(deal_qs.aggregate(s=Sum("amount"))["s"] or 0),
            "deal_paid_amount": float(deal_paid),
            "deal_balance": float(deal_qs.aggregate(s=Sum("amount"))["s"] or 0) - float(deal_paid),
            # Status breakdowns
            "deals_by_status": deal_status,
            "deals_by_payment_status": payment_status,
        })


class AdminReportView(APIView):
    """Admin: partner rankings, total applicants by status, revenue + commission totals."""
    permission_classes = [IsAuthenticated, IsAdminOrStaff]

    def get(self, request):
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        partner_id = request.query_params.get("partner_id")
        
        # Base querysets
        applicant_qs = Applicant.objects.all()
        deal_qs = Deal.objects.all()
        
        if from_date:
            applicant_qs = applicant_qs.filter(created_at__date__gte=from_date)
            deal_qs = deal_qs.filter(created_at__date__gte=from_date)
        if to_date:
            applicant_qs = applicant_qs.filter(created_at__date__lte=to_date)
            deal_qs = deal_qs.filter(created_at__date__lte=to_date)
        if partner_id:
            applicant_qs = applicant_qs.filter(partner_id=partner_id)
            deal_qs = deal_qs.filter(partner_id=partner_id)
        
        # Applicant stats by status
        applicant_by_status = dict(
            applicant_qs.values("status").annotate(count=Count("id")).values_list("status", "count")
        )
        
        # Deal stats by status
        deal_by_status = {}
        for status_choice in Deal.STATUS_CHOICES:
            status_value = status_choice[0]
            count = deal_qs.filter(status=status_value).count()
            deal_by_status[status_value] = count
        
        # Financial totals
        total_revenue = Payment.objects.filter(
            status=Payment.STATUS_PAID,
            applicant__in=applicant_qs,
        ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        
        total_commission = Commission.objects.filter(
            applicant__in=applicant_qs,
        ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        
        deal_total_amount = deal_qs.aggregate(s=Sum("amount"))["s"] or Decimal("0")
        deal_paid_amount = deal_qs.aggregate(s=Sum("paid_amount"))["s"] or Decimal("0")
        
        # Partner rankings
        partners = Partner.objects.filter(status=Partner.STATUS_APPROVED)
        rankings = []
        for p in partners:
            p_applicants = applicant_qs.filter(partner=p)
            p_deals = deal_qs.filter(partner=p)
            
            cnt = p_applicants.count()
            deal_count = p_deals.count()
            rev = Payment.objects.filter(
                applicant__partner=p,
                status=Payment.STATUS_PAID,
                applicant__in=p_applicants,
            ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
            
            # Conversion: approved/completed deals
            converted = p_deals.filter(
                status__in=[Deal.STATUS_APPROVED, Deal.STATUS_COMPLETED]
            ).count()
            
            rankings.append({
                "partner_id": p.id,
                "company_name": p.company_name,
                "applicants_count": cnt,
                "deals_count": deal_count,
                "revenue": float(rev),
                "converted_deals": converted,
            })
        
        rankings.sort(key=lambda x: x["revenue"], reverse=True)
        
        return Response({
            "from_date": from_date,
            "to_date": to_date,
            "applicants_by_status": applicant_by_status,
            "deals_by_status": deal_by_status,
            "total_revenue": float(total_revenue),
            "total_commission": float(total_commission),
            "deal_total_amount": float(deal_total_amount),
            "deal_paid_amount": float(deal_paid_amount),
            "partner_rankings": rankings,
        })


def _csv_response(filename, rows, headers):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


class ExportPartnerReportCSVView(APIView):
    """Partner: export own report as CSV."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = get_partner_for_request(request)
        if partner is None:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        from_date = request.query_params.get("from_date", "")
        to_date = request.query_params.get("to_date", "")
        
        # Get deals for export
        deal_qs = Deal.objects.filter(partner=partner)
        if from_date:
            deal_qs = deal_qs.filter(created_at__date__gte=from_date)
        if to_date:
            deal_qs = deal_qs.filter(created_at__date__lte=to_date)
        
        rows = []
        for d in deal_qs[:5000]:
            rows.append([
                d.id,
                d.applicant.full_name if d.applicant else '',
                d.applicant.email if d.applicant else '',
                d.status,
                d.payment_status,
                float(d.amount),
                float(d.paid_amount),
                float(d.amount) - float(d.paid_amount),
                d.created_at.date()
            ])
        return _csv_response(
            f"partner_report_{partner.id}_{datetime.now().strftime('%Y%m%d')}.csv",
            rows,
            ["id", "applicant_name", "email", "deal_status", "payment_status", "amount", "paid", "balance", "created_at"],
        )


class ExportAdminReportCSVView(APIView):
    """Admin: export partner rankings as CSV."""
    permission_classes = [IsAuthenticated, IsAdminOrStaff]

    def get(self, request):
        from_date = request.query_params.get("from_date", "")
        to_date = request.query_params.get("to_date", "")
        partner_id = request.query_params.get("partner_id")
        
        # Base querysets
        applicant_qs = Applicant.objects.all()
        deal_qs = Deal.objects.all()
        
        if from_date:
            applicant_qs = applicant_qs.filter(created_at__date__gte=from_date)
            deal_qs = deal_qs.filter(created_at__date__gte=from_date)
        if to_date:
            applicant_qs = applicant_qs.filter(created_at__date__lte=to_date)
            deal_qs = deal_qs.filter(created_at__date__lte=to_date)
        if partner_id:
            applicant_qs = applicant_qs.filter(partner_id=partner_id)
            deal_qs = deal_qs.filter(partner_id=partner_id)
        
        # Build rows
        partners = Partner.objects.filter(status=Partner.STATUS_APPROVED)
        rows = []
        for p in partners:
            p_applicants = applicant_qs.filter(partner=p)
            p_deals = deal_qs.filter(partner=p)
            
            cnt = p_applicants.count()
            deal_count = p_deals.count()
            rev = Payment.objects.filter(
                applicant__partner=p,
                status=Payment.STATUS_PAID,
                applicant__in=p_applicants,
            ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
            
            converted = p_deals.filter(
                status__in=[Deal.STATUS_APPROVED, Deal.STATUS_COMPLETED]
            ).count()
            
            rows.append([p.id, p.company_name, cnt, deal_count, float(rev), converted])
        
        return _csv_response(
            f"admin_report_{datetime.now().strftime('%Y%m%d')}.csv",
            rows,
            ["partner_id", "company_name", "applicants_count", "deals_count", "revenue", "converted"],
        )


class ExportPartnerReportPDFView(APIView):
    """Partner: export own report as PDF (simple table)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = get_partner_for_request(request)
        if partner is None:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        from_date = request.query_params.get("from_date", "")
        to_date = request.query_params.get("to_date", "")
        
        deal_qs = Deal.objects.filter(partner=partner)
        if from_date:
            deal_qs = deal_qs.filter(created_at__date__gte=from_date)
        if to_date:
            deal_qs = deal_qs.filter(created_at__date__lte=to_date)
        
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="partner_report_{partner.id}.pdf"'
        doc = SimpleDocTemplate(response, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = [
            Paragraph(f"Partner Report: {partner.company_name}", styles["Title"]),
            Spacer(1, 0.2 * inch),
            Paragraph(f"Date range: {from_date or 'start'} to {to_date or 'end'}", styles["Normal"]),
            Spacer(1, 0.3 * inch),
        ]
        data = [["ID", "Applicant", "Status", "Payment", "Amount", "Created"]]
        for d in deal_qs[:500]:
            data.append([
                str(d.id),
                d.applicant.full_name if d.applicant else '',
                d.status,
                d.payment_status,
                f"${d.amount}",
                str(d.created_at.date())
            ])
        t = Table(data)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(t)
        doc.build(elements)
        return response
