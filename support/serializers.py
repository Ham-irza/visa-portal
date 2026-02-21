from rest_framework import serializers
from .models import Ticket, TicketMessage
from accounts.models import Partner


class TicketMessageSerializer(serializers.ModelSerializer):
    author_email = serializers.CharField(source="author.email", read_only=True)

    class Meta:
        model = TicketMessage
        fields = ["id", "author", "author_email", "body", "is_staff_reply", "created_at"]
        read_only_fields = ["author", "is_staff_reply", "created_at"]


class TicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    partner_name = serializers.CharField(source="partner.company_name", read_only=True)

    class Meta:
        model = Ticket
        fields = ["id", "partner", "partner_name", "subject", "status", "category", "priority", "messages", "created_at", "updated_at"]
        read_only_fields = ["partner", "created_at", "updated_at"]


class TicketListSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source="partner.company_name", read_only=True)

    class Meta:
        model = Ticket
        fields = ["id", "partner_name", "subject", "status", "category", "priority", "created_at"]


class TicketCreateSerializer(serializers.ModelSerializer):
    initial_message = serializers.CharField(write_only=True)
    category = serializers.ChoiceField(choices=Ticket.CATEGORY_CHOICES, default=Ticket.CATEGORY_GENERAL)
    priority = serializers.ChoiceField(choices=Ticket.PRIORITY_CHOICES, default=Ticket.PRIORITY_MEDIUM)

    class Meta:
        model = Ticket
        fields = ["subject", "initial_message", "category", "priority"]

    def create(self, validated_data):
        msg = validated_data.pop("initial_message")
        partner = self.context["request"].user.partner
        ticket = Ticket.objects.create(
            partner=partner, 
            subject=validated_data["subject"],
            category=validated_data.get("category", Ticket.CATEGORY_GENERAL),
            priority=validated_data.get("priority", Ticket.PRIORITY_MEDIUM)
        )
        TicketMessage.objects.create(
            ticket=ticket,
            author=self.context["request"].user,
            body=msg,
            is_staff_reply=False,
        )
        return ticket


class TicketCreateResponseSerializer(serializers.ModelSerializer):
    """Response after create: full ticket with messages."""
    messages = TicketMessageSerializer(many=True, read_only=True)
    partner_name = serializers.CharField(source="partner.company_name", read_only=True)

    class Meta:
        model = Ticket
        fields = ["id", "partner", "partner_name", "subject", "status", "messages", "created_at", "updated_at"]
