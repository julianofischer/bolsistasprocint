# myapp/urls.py
from django.urls import path
from reports.api import ReportListView
from reports import views

urlpatterns = [
    path("meusrelatorios", ReportListView.as_view(), name="report-list"),
]
