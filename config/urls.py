"""
Partner Portal – Root URL configuration.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from applicants.dashboard_views import DashboardStatsView, AdminStatsView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/dashboard/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("api/dashboard/admin-stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("api/", include("applicants.urls")),
    path("api/", include("documents.urls")),
    path("api/", include("payments.urls")),
    path("api/", include("commissions.urls")),
    path("api/", include("reports.urls")),
    path("api/", include("support.urls")),
    path("api/", include("deals.urls")),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
