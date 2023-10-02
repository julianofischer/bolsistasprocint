# myapp/urls.py
from django.urls import path
# from reports.api import ReportListView
from reports import views

urlpatterns = [
    path("", views.UserReportsListView.as_view(), name="user-reports"),
    path("<int:report_id>", views.ReportEntriesListView.as_view(), name="report-entries"),
    path("<int:report_id>/entry/add", views.ReportEntryCreateView.as_view(), name="create_report_entry"),
    path("<int:report_id>/entry/<int:entry_id>/edit", views.ReportEntryCreateView.as_view(), name="edit-entry"),
]
