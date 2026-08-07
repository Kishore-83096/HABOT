from django.urls import path

from .views import AvailabilityAPIView, LSADetailAPIView, LSAScheduleAPIView, LSASearchAPIView

urlpatterns = [
    path("search/", LSASearchAPIView.as_view(), name="lsa-search"),
    path("<uuid:pk>/", LSADetailAPIView.as_view(), name="lsa-detail"),
    path("<uuid:pk>/availability/", AvailabilityAPIView.as_view(), name="lsa-availability"),
    path("<uuid:pk>/schedule/", LSAScheduleAPIView.as_view(), name="lsa-schedule"),
]
