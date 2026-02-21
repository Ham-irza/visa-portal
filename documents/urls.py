from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet
from .views import ServiceTypeViewSet, RequiredDocumentViewSet

router = DefaultRouter()
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"service-types", ServiceTypeViewSet, basename="service-type")
router.register(r"document-requirements", RequiredDocumentViewSet, basename="document-requirement")

urlpatterns = [
    path("", include(router.urls)),
]
