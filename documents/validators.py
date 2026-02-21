"""
Secure file upload: allowed extensions and MIME, size.
"""
import os
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_upload_file(file):
    """Validate extension and size. MIME can be checked in view with python-magic if needed."""
    ext = os.path.splitext(getattr(file, "name", "") or "")[1].lower()
    allowed = getattr(settings, "ALLOWED_UPLOAD_EXTENSIONS", {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"})
    if ext not in allowed:
        raise ValidationError(f"File type not allowed. Allowed: {', '.join(sorted(allowed))}")
    max_size = getattr(settings, "FILE_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024)
    if file.size > max_size:
        raise ValidationError(f"File too large. Max size: {max_size // (1024*1024)} MB")
