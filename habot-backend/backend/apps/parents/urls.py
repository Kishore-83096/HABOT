from django.urls import path

from .views import ParentBookingStatusAPIView, ParentDashboardAPIView, ParentDetailAPIView, ParentListAPIView

urlpatterns = [
    path("", ParentListAPIView.as_view(), name="parent-list"),
    path("<uuid:pk>/bookings/", ParentBookingStatusAPIView.as_view(), name="parent-booking-status"),
    path("<uuid:pk>/dashboard/", ParentDashboardAPIView.as_view(), name="parent-dashboard"),
    path("<uuid:pk>/", ParentDetailAPIView.as_view(), name="parent-detail"),
]
