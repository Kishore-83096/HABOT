from django.urls import path

from .views import BookingCancelAPIView, BookingDetailAPIView, BookingListCreateAPIView

urlpatterns = [
    path("", BookingListCreateAPIView.as_view(), name="booking-list-create"),
    path("<uuid:pk>/", BookingDetailAPIView.as_view(), name="booking-detail"),
    path("<uuid:pk>/cancel/", BookingCancelAPIView.as_view(), name="booking-cancel"),
]
