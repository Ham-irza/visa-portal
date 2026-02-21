import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse

from .models import Payment
from .serializers import PaymentSerializer, PaymentListSerializer
from core.mixins import filter_queryset_by_partner
from core.permissions import PartnerDataIsolation


class PaymentViewSet(viewsets.ModelViewSet):
    """Payments: partner sees only their applicants'; admin sees all."""
    permission_classes = [PartnerDataIsolation]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["applicant", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Payment.objects.all().select_related("applicant", "applicant__partner")
        return filter_queryset_by_partner(qs, self.request, "applicant__partner")

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        return PaymentSerializer

    @action(detail=True, methods=["get"], url_path="download-receipt")
    def download_receipt(self, request, pk=None):
        """Download invoice/receipt file if present."""
        payment = self.get_object()
        if not payment.receipt_file:
            return Response({"detail": "No receipt file."}, status=status.HTTP_404_NOT_FOUND)
        path = payment.receipt_file.path
        if not os.path.isfile(path):
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)
        name = os.path.basename(path)
        return FileResponse(payment.receipt_file.open("rb"), as_attachment=True, filename=name)
