from django.urls import path

from .views import AdminAnalyticsView

urlpatterns = [
    path("analytics/admin/", AdminAnalyticsView.as_view(), name="admin-analytics"),
]


