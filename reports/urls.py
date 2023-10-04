# myapp/urls.py
from django.urls import path
# from reports.api import ReportListView
from reports import views

urlpatterns = [
    path("", views.UserReportsListView.as_view(), name="user-reports"),
    path("<int:report_id>/", views.ReportEntriesListView.as_view(), name="report-entries"),
    path('<int:report_id>/pdf/', views.PDFView.as_view(), name='generate_pdf'),
    path("<int:report_id>/entregar", views.ReportSubmissionCreateView.as_view(), name="submit_report"),
    path("<int:report_id>/entrega/<int:pk>", views.ReportSubmissionDetailView.as_view(), name="report_submission_detail"),
    path("<int:report_id>/entry/add/", views.ReportEntryCreateView.as_view(), name="create_report_entry"),
    path("<int:report_id>/entry/<int:pk>/edit/", views.ReportEntryUpdateView.as_view(), name="edit_report_entry"),
    path("<int:report_id>/entry/<int:pk>/delete/", views.ReportEntryDeleteView.as_view(), name="delete_report_entry"),
]
