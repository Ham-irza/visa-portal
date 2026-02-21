from django.urls import path
from .views import (
    PartnerReportView,
    AdminReportView,
    ExportPartnerReportCSVView,
    ExportAdminReportCSVView,
    ExportPartnerReportPDFView,
)

urlpatterns = [
    path("reports/partner/", PartnerReportView.as_view(), name="report-partner"),
    path("reports/admin/", AdminReportView.as_view(), name="report-admin"),
    path("reports/partner/export/csv/", ExportPartnerReportCSVView.as_view(), name="report-partner-csv"),
    path("reports/admin/export/csv/", ExportAdminReportCSVView.as_view(), name="report-admin-csv"),
    path("reports/partner/export/pdf/", ExportPartnerReportPDFView.as_view(), name="report-partner-pdf"),
]
