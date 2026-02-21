from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
import os

from .models import Document
from .serializers import DocumentSerializer, DocumentListSerializer, DocumentStatusSerializer
from .models import ServiceType, RequiredDocument
from .serializers import ServiceTypeSerializer, RequiredDocumentSerializer
from applicants.models import Applicant
from core.mixins import filter_queryset_by_partner, get_partner_for_request
from core.permissions import PartnerDataIsolation, IsAdminOrStaff


class DocumentViewSet(viewsets.ModelViewSet):
    """Documents: list/create/retrieve/update/destroy. Partner sees only own applicants' docs."""
    permission_classes = [PartnerDataIsolation]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["applicant", "document_type", "status"]
    ordering = ["-uploaded_at"]

    def get_queryset(self):
        qs = Document.objects.all().select_related("applicant", "applicant__partner")
        # Filter by partner through applicant
        partner = get_partner_for_request(self.request)
        if partner is not None:
            qs = qs.filter(applicant__partner=partner)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentListSerializer
        if self.action in ("partial_update", "update") and getattr(self.request.user, "is_staff_or_admin", False):
            return DocumentStatusSerializer
        return DocumentSerializer

    def perform_create(self, serializer):
        applicant = serializer.validated_data["applicant"]
        partner = get_partner_for_request(self.request)
        # If request is coming from a Partner, ensure the applicant belongs to them
        if partner is not None:
            if applicant.partner_id != partner.id:
                raise PermissionError("Applicant does not belong to your partner account.")
        else:
            # No partner (individual flow) — allow if the logged-in user owns the applicant
            if getattr(applicant, 'applicant_user', None) is not None:
                if applicant.applicant_user != self.request.user:
                    raise PermissionError("You do not have permission to upload documents for this applicant.")
            else:
                # Applicant is not linked to a user and no partner present — deny
                raise PermissionError("Applicant must belong to your partner account or be owned by you.")
        if serializer.validated_data.get("file"):
            serializer.validated_data["original_filename"] = serializer.validated_data["file"].name
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        """Secure download: only owner or admin."""
        doc = self.get_object()
        if not doc.file:
            return Response({"detail": "No file."}, status=status.HTTP_404_NOT_FOUND)
        path = doc.file.path
        if not os.path.isfile(path):
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)
        name = doc.original_filename or os.path.basename(path)
        response = FileResponse(doc.file.open("rb"), as_attachment=True, filename=name)
        return response


class ServiceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Expose service/visa types and their document requirements."""
    queryset = ServiceType.objects.all()
    serializer_class = ServiceTypeSerializer


class RequiredDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """Expose required documents for services. Admins can extend via admin site."""
    queryset = RequiredDocument.objects.select_related("service").all()
    serializer_class = RequiredDocumentSerializer

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        """Secure download: only owner or admin."""
        doc = self.get_object()
        if not doc.file:
            return Response({"detail": "No file."}, status=status.HTTP_404_NOT_FOUND)
        path = doc.file.path
        if not os.path.isfile(path):
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)
        name = doc.original_filename or os.path.basename(path)
        response = FileResponse(doc.file.open("rb"), as_attachment=True, filename=name)
        return response

    def partial_update(self, request, *args, **kwargs):
        """Admin can update status/notes; partner cannot."""
        if getattr(request.user, "is_staff_or_admin", False):
            return super().partial_update(request, *args, **kwargs)
        return Response({"detail": "Only staff can update document status."}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        if getattr(request.user, "is_staff_or_admin", False):
            return super().update(request, *args, **kwargs)
        return Response({"detail": "Only staff can update document status."}, status=status.HTTP_403_FORBIDDEN)
