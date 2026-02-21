"""
URL configuration for Deals API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DealViewSet, DealNoteViewSet, DealStatsViewSet

router = DefaultRouter()
router.register(r'deals', DealViewSet, basename='deal')
router.register(r'deal-notes', DealNoteViewSet, basename='deal-note')
router.register(r'deals-stats', DealStatsViewSet, basename='deal-stats')

urlpatterns = [
    path('', include(router.urls)),
]
