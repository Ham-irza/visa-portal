from rest_framework import serializers
from .models import Commission, CommissionRule


class CommissionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionRule
        fields = [
            "id",
            "tier",
            "base_rate",
            "bonus_rate",
            "threshold",
        ]


class CommissionSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source="applicant.full_name", read_only=True)
    partner_name = serializers.CharField(source="applicant.partner.company_name", read_only=True)

    class Meta:
        model = Commission
        fields = [
            "id",
            "applicant",
            "applicant_name",
            "partner_name",
            "amount",
            "currency",
            "status",
            "paid_at",
            "payout_reference",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CommissionListSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source="applicant.full_name", read_only=True)

    class Meta:
        model = Commission
        fields = ["id", "applicant", "applicant_name", "amount", "currency", "status", "paid_at", "created_at"]