from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Ticket, TicketMessage
from .serializers import (
    TicketSerializer,
    TicketListSerializer,
    TicketCreateSerializer,
    TicketCreateResponseSerializer,
    TicketMessageSerializer,
)
from core.mixins import get_partner_for_request
from core.permissions import IsAdminOrStaff


class TicketViewSet(viewsets.ModelViewSet):
    """Tickets: partner sees own, creates with initial message; admin sees all and can reply/update status."""
    permission_classes = [IsAuthenticated]
    filter_backends = []
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Ticket.objects.all().select_related("partner").prefetch_related("messages", "messages__author")
        partner = get_partner_for_request(self.request)
        if partner is not None:
            qs = qs.filter(partner=partner)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return TicketCreateSerializer
        if self.action == "list":
            return TicketListSerializer
        return TicketSerializer

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        if not getattr(request.user, "is_partner", False):
            return Response(
                {"detail": "Only partners can create tickets."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if getattr(request.user, "is_staff_or_admin", False):
            return super().partial_update(request, *args, **kwargs)
        return Response({"detail": "Only staff can update ticket status."}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        if getattr(request.user, "is_staff_or_admin", False):
            return super().update(request, *args, **kwargs)
        return Response({"detail": "Only staff can update ticket."}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=["post"], url_path="reply")
    def reply(self, request, pk=None):
        """Add a message to the ticket. Partner or staff."""
        ticket = self.get_object()
        body = request.data.get("body", "").strip()
        if not body:
            return Response({"detail": "Body is required."}, status=status.HTTP_400_BAD_REQUEST)
        is_staff = getattr(request.user, "is_staff_or_admin", False)
        TicketMessage.objects.create(
            ticket=ticket,
            author=request.user,
            body=body,
            is_staff_reply=is_staff,
        )
        return Response(TicketMessageSerializer(TicketMessage.objects.filter(ticket=ticket).order_by("created_at").last()).data)