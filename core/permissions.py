"""
Role-based permissions and partner data isolation.
Partners can only access their own data; Admin/Staff can access all.
"""
from rest_framework import permissions

class IsAdminOrStaff(permissions.BasePermission):
    """Only admin or staff users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "is_staff_or_admin", False))

class IsPartner(permissions.BasePermission):
    """Only partner users (not admin/staff acting as partner)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "is_partner", False))

def _get_partner_from_obj(obj):
    """Helper: Get Partner instance from an object (Applicant, Document, etc)."""
    # 1. Direct link (e.g., Applicant.partner)
    if hasattr(obj, 'partner'):
        return obj.partner
    
    # 2. Indirect link via Applicant (e.g., Document.applicant.partner)
    if hasattr(obj, 'applicant') and hasattr(obj.applicant, 'partner'):
        return obj.applicant.partner
        
    return None

class PartnerDataIsolation(permissions.BasePermission):
    """
    Strict Data Isolation.
    - Admins: Can see/edit everything.
    - Partners: Can ONLY see/edit objects linked to their PartnerProfile.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Admin/Staff can do anything
        if getattr(request.user, "is_staff_or_admin", False) or request.user.is_superuser:
            return True
            
        # Check if the object belongs to the partner
        obj_partner = _get_partner_from_obj(obj)
        
        # If the object has no partner link, allow access if the object is owned
        # by the logged-in user (applicant-owned flow). This supports individual
        # users managing their own applications/documents.
        if obj_partner is None:
            # Support Document objects (obj may be Document) -> check obj.applicant.applicant_user
            applicant = getattr(obj, 'applicant', None)
            if applicant is not None and getattr(applicant, 'applicant_user', None) == request.user:
                return True
            return False
            
        # Does the object's partner ID match the logged-in user's partner ID?
        # Note: request.user.partner is the PartnerProfile. 
        # obj_partner is also a PartnerProfile.
        return obj_partner.id == request.user.partner.id

IsPartnerOwnerOrAdmin = PartnerDataIsolation