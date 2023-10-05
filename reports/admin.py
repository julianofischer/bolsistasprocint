from django.contrib import admin

# Register your models here.

from .models import Report, ReportEntry, ReportSubmission, CustomUser, ReportSubmission, PendingReportSubmission

class RefMonthYearFilter(admin.SimpleListFilter):
    title = 'Ano'
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        # Retrieve a list of distinct years from the database
        return (
            (str(year.year), str(year.year))
            for year in model_admin.model.objects.dates('ref_month', 'year')
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(ref_month__year=self.value())

class RefMonthFilter(admin.SimpleListFilter):
    title = 'Mês'
    parameter_name = 'month'

    def lookups(self, request, model_admin):
        # Retrieve a list of distinct months from the database
        return (
            (str(month.month), month.strftime('%B'))
            for month in model_admin.model.objects.dates('ref_month', 'month')
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(ref_month__month=self.value())
    
class ReportAdmin(admin.ModelAdmin):
    list_display = ("user", "ref_month", "total_hours")
    list_filter = ("user", RefMonthYearFilter, RefMonthFilter)

class ReportEntryAdmin(admin.ModelAdmin):
    list_display = ("report", "description", "date", "init_hour", "end_hour", "hours")
    list_filter = ("report", "date")

class ReportSubmissionAdmin(admin.ModelAdmin):
    list_display = ("report", "submitted_at", "status", "reviewer")
    list_filter = ( "status",)

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "scholarship", "role", "eixo", "ch")


class PendingReportSubmissionAdmin(admin.ModelAdmin):
    list_display = ("report_user", "report_ref_month", "submitted_at", "status", "reviewer", "pdf_file")
    list_filter = ("status",)
    actions = ["aprovar", "rejeitar"]

    def has_add_permission(self, request):
        return False

    def aprovar(self, request, queryset):
        for submission in queryset:
            submission.status = ReportSubmission.ReportStatus.APPROVED
            submission.save()

    def rejeitar(self, request, queryset):
        for submission in queryset:
            submission.status = ReportSubmission.ReportStatus.REJECTED
            submission.save()
    
    def report_ref_month(self, obj):
        r = f"{obj.report.ref_month.strftime('%B')}/{obj.report.ref_month.year}"
        return r
    
    def report_user(self, obj):
        return obj.report.user.name

    report_ref_month.short_description = 'Mês de referência'
    report_user.short_description = 'Bolsista'

admin.site.register(Report, ReportAdmin)
admin.site.register(ReportEntry, ReportEntryAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(ReportSubmission, ReportSubmissionAdmin)
admin.site.register(PendingReportSubmission, PendingReportSubmissionAdmin)