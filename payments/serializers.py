from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source="applicant.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "applicant",
            "applicant_name",
            "amount",
            "currency",
            "status",
            "payment_date",
            "invoice_number",
            "receipt_file",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class PaymentListSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source="applicant.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "applicant", "applicant_name", "amount", "currency", "status", "payment_date", "created_at"]
