from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommissionViewSet, CommissionRuleViewSet

router = DefaultRouter()
router.register(r"commissions", CommissionViewSet, basename="commission")
router.register(r"commission-rules", CommissionRuleViewSet, basename="commission-rule")

urlpatterns = [
    path("", include(router.urls)),
]