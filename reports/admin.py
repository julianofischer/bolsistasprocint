from django.contrib import admin

# Register your models here.

from .models import Report, ReportEntry, ReportSubmission

admin.site.register(Report)
admin.site.register(ReportEntry)
admin.site.register(ReportSubmission)
