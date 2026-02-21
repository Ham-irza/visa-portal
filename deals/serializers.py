"""
Serializers for Deals API.
"""
from rest_framework import serializers
from .models import Deal, DealNote
from applicants.models import Applicant
from accounts.models import User, Partner


class DealNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    
    class Meta:
        model = DealNote
        fields = "__all__"
        read_only_fields = ["author", "created_at"]


class ApplicantMinimalSerializer(serializers.ModelSerializer):
    """Minimal applicant info for embedding in Deal."""
    class Meta:
        model = Applicant
        fields = [
            "id", "full_name", "phone", "email", "passport_number",
            "nationality", "destination_country", "visa_type"
        ]


class DealSerializer(serializers.ModelSerializer):
    """Full serializer for Deal with all fields."""
    deal_id = serializers.CharField(read_only=True)
    balance = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    partner_name = serializers.CharField(source="partner.company_name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.get_full_name", read_only=True)
    applicant_details = ApplicantMinimalSerializer(source="applicant", read_only=True)
    
    # Flat applicant fields for frontend
    applicant_name = serializers.CharField(source="applicant.full_name", read_only=True)
    applicant_phone = serializers.CharField(source="applicant.phone", read_only=True)
    applicant_email = serializers.CharField(source="applicant.email", read_only=True)
    applicant_passport = serializers.CharField(source="applicant.passport_number", read_only=True)
    
    notes = DealNoteSerializer(many=True, read_only=True)
    
    # For creating/updating
    applicant_id = serializers.PrimaryKeyRelatedField(
        queryset=Applicant.objects.all(),
        source="applicant",
        write_only=True
    )
    
    class Meta:
        model = Deal
        fields = [
            "id", "deal_id", "applicant", "applicant_id", "applicant_details",
            "applicant_name", "applicant_phone", "applicant_email", "applicant_passport",
            "partner", "partner_name", "assigned_to", "assigned_to_name",
            "visa_type", "destination_country", "status", "payment_status",
            "amount", "paid_amount", "balance", "currency", "is_paid",
            "partner_notes", "internal_notes", "notes",
            "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "deal_id", "partner", "paid_amount", "payment_status",
            "created_at", "updated_at"
        ]
    
    def create(self, validated_data):
        # Auto-set partner from request
        from core.mixins import get_partner_for_request
        partner = get_partner_for_request(self.context["request"])
        if partner:
            validated_data["partner"] = partner
        return super().create(validated_data)
    
    def validate_applicant_id(self, value):
        """Validate that applicant belongs to the partner (for partners)."""
        request = self.context.get("request")
        if not request:
            return value
            
        user = request.user
        if getattr(user, "is_staff_or_admin", False):
            return value
        
        # Check if applicant belongs to the partner
        try:
            partner = user.partner
            if value.partner != partner:
                raise serializers.ValidationError(
                    "You can only create deals for your own applicants."
                )
        except (Partner.DoesNotExist, AttributeError):
            pass
        
        return value


class DealListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list view."""
    deal_id = serializers.CharField(read_only=True)
    balance = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    partner_name = serializers.CharField(source="partner.company_name", read_only=True)
    applicant_name = serializers.CharField(source="applicant.full_name", read_only=True)
    applicant_phone = serializers.CharField(source="applicant.phone", read_only=True)
    applicant_email = serializers.CharField(source="applicant.email", read_only=True)
    
    class Meta:
        model = Deal
        fields = [
            "id", "deal_id", "applicant", "applicant_name", "applicant_phone", "applicant_email",
            "partner", "partner_name", "visa_type", "destination_country",
            "status", "payment_status", "amount", "paid_amount", "balance", "currency",
            "created_at", "updated_at"
        ]


class DealCreateSerializer(serializers.ModelSerializer):
    """Serializer specifically for creating deals."""
    # Accept both applicant and applicant_id
    applicant = serializers.PrimaryKeyRelatedField(
        queryset=Applicant.objects.all(),
    )
    
    class Meta:
        model = Deal
        fields = [
            "applicant", "visa_type", "destination_country", 
            "amount", "currency", "partner_notes"
        ]
    
    def validate_applicant(self, value):
        """Validate that applicant belongs to the partner (for partners)."""
        request = self.context.get("request")
        if not request:
            return value
            
        user = request.user
        if getattr(user, "is_staff_or_admin", False):
            return value
        
        # Check if applicant belongs to the partner
        from accounts.models import Partner
        try:
            partner = user.partner
            if value.partner != partner:
                raise serializers.ValidationError(
                    "You can only create deals for your own applicants."
                )
        except (Partner.DoesNotExist, AttributeError):
            pass
        
        return value
    
    def create(self, validated_data):
        # Auto-set partner from request or from applicant
        from core.mixins import get_partner_for_request
        request = self.context.get("request")
        
        # First try to get partner from request
        partner = get_partner_for_request(request) if request else None
        
        # If no partner from request, get from the applicant's partner
        if not partner and validated_data.get('applicant'):
            applicant_id = validated_data.get('applicant')
            if isinstance(applicant_id, int):
                # Fetch the applicant to get its partner
                try:
                    applicant = Applicant.objects.get(id=applicant_id)
                    partner = applicant.partner
                except Applicant.DoesNotExist:
                    pass
            elif hasattr(applicant_id, 'partner'):
                partner = applicant_id.partner
        
        if not partner:
            raise serializers.ValidationError({
                "partner": "Unable to determine partner for this deal. Please ensure you are logged in as a partner or the applicant has a partner."
            })
        
        validated_data["partner"] = partner
        return super().create(validated_data)


class DealUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating deals - different permissions for partners vs staff."""
    
    # Allow reassigning partner (admin only)
    partner_id = serializers.PrimaryKeyRelatedField(
        queryset=Partner.objects.all(),
        source="partner",
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Deal
        fields = [
            "visa_type", "destination_country", "amount", 
            "partner_notes", "internal_notes", 
            "status", "payment_status", "paid_amount", "assigned_to", "partner_id"
        ]
    
    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None
        
        # Partners cannot change these fields
        if user and not getattr(user, "is_staff_or_admin", False):
            restricted_fields = ["status", "payment_status", "paid_amount", "assigned_to", "internal_notes", "partner_id"]
            for field in restricted_fields:
                if field in attrs:
                    raise serializers.ValidationError({
                        field: "You don't have permission to modify this field."
                    })
        
        return attrs
