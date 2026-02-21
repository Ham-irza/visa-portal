"""
Queryset filtering: partners see only their data; admin/staff see all.
"""
from accounts.models import Partner


def get_partner_for_request(request):
    """Return Partner instance for request user, or None if admin/staff."""
    if not request.user.is_authenticated:
        return None
    if getattr(request.user, "is_staff_or_admin", False):
        return None
    try:
        return request.user.partner
    except (Partner.DoesNotExist, AttributeError):
        return None


def filter_queryset_by_partner(queryset, request, partner_field="partner"):
    """
    Restrict queryset to partner's data. Admin/staff get full queryset.
    queryset model must have a FK like 'partner' or 'assigned_partner'.
    """
    partner = get_partner_for_request(request)
    if partner is None:
        return queryset
    return queryset.filter(**{partner_field: partner})
