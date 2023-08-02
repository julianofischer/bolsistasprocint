# myapp/urls.py
from django.urls import path
from .api import ReportListView

urlpatterns = [
    path("/meusrelatorios", ReportListView.as_view(), name="report-list"),
]
