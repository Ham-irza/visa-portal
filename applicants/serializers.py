from rest_framework import serializers
from .models import Applicant
from accounts.models import Partner

class ApplicantSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source="partner.company_name", read_only=True)
    owner_email = serializers.CharField(source="applicant_user.email", read_only=True)

    class Meta:
        model = Applicant
        # automatically include ALL fields from the model
        fields = "__all__"
        # Prevent partners from editing these system fields
        read_only_fields = ["id", "created_at", "updated_at", "partner", "partner_name", "applicant_user"]

    def validate_extra_data(self, value):
        """Ensure extra_data is a valid dictionary (JSON object)."""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError("Extra data must be a valid JSON object.")
        return value

class ApplicantListSerializer(serializers.ModelSerializer):
    """Lighter serializer for the list view (fewer fields to load faster)."""
    partner_name = serializers.CharField(source="partner.company_name", read_only=True)

    class Meta:
        model = Applicant
        fields = [
            "id",
            "partner_name",
            "full_name",
            "passport_number",
            "destination_country",
            "visa_type",
            "status",
            "created_at",
            "email",
            "phone",
        ]
