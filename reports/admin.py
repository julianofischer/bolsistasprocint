from django.contrib import admin
from django import forms

# Register your models here.

from .models import (
    Report,
    ReportEntry,
    ReportSubmission,
    CustomUser,
    ReportSubmission,
    PendingReportSubmission,
    Scholarship,
    Eixo,
    Role,
)

from django.contrib.admin import AdminSite

class CustomAdminSite(AdminSite):
    site_title = 'Bolsitas PROCINT'  # Replace with your desired title
    site_header = 'Administração Bolsistas PROCINT'  # Optional: Replace with a custom header text

custom_admin_site = CustomAdminSite(name='customadmin')
admin.site = custom_admin_site


class RefMonthYearFilter(admin.SimpleListFilter):
    title = "Ano"
    parameter_name = "year"

    def lookups(self, request, model_admin):
        # Retrieve a list of distinct years from the database
        return (
            (str(year.year), str(year.year))
            for year in model_admin.model.objects.dates("ref_month", "year")
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(ref_month__year=self.value())


class RefMonthFilter(admin.SimpleListFilter):
    title = "Mês"
    parameter_name = "month"

    def lookups(self, request, model_admin):
        # Retrieve a list of distinct months from the database
        return (
            (str(month.month), month.strftime("%B"))
            for month in model_admin.model.objects.dates("ref_month", "month")
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
    list_filter = ("status",)


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "scholarship", "role", "eixo", "ch")
    list_filter = ("is_active",)

    actions = ["ativar", "desativar"]

    def ativar(self, request, queryset):
        queryset.update(is_active=True)
    
    def desativar(self, request, queryset):
        queryset.update(is_active=False)


class PendingReportSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "report_user",
        "report_ref_month",
        "submitted_at",
        "status",
        "reviewer",
        "pdf_file",
    )
    list_filter = ("status",)
    actions = ["aprovar", "rejeitar"]
    fields = ("status", "reason")
    # change_list_template = "reports/admin/custom_change_list.html"
    
    class CustomActionForm(admin.helpers.ActionForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["reason"] = forms.CharField(required=False, label="Motivo")

    action_form = CustomActionForm

    def has_add_permission(self, request):
        return False

    def _change_status(self, request, queryset, status):
        for submission in queryset:
            submission.reason = request.POST["reason"]
            submission.reviewer = request.user
            submission.status = status
            submission.save()

    def aprovar(self, request, queryset):
        self._change_status(request, queryset, ReportSubmission.ReportStatus.APPROVED)

    def rejeitar(self, request, queryset):
        self._change_status(request, queryset, ReportSubmission.ReportStatus.REJECTED)

    def report_ref_month(self, obj):
        r = f"{obj.report.ref_month.strftime('%B')}/{obj.report.ref_month.year}"
        return r

    def report_user(self, obj):
        return obj.report.user.name

    report_ref_month.short_description = "Mês de referência"
    report_user.short_description = "Bolsista"



admin.site.register(Scholarship)
admin.site.register(Eixo)
admin.site.register(Role)

# Custom admin classes
admin.site.register(Report, ReportAdmin)
admin.site.register(ReportEntry, ReportEntryAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(ReportSubmission, ReportSubmissionAdmin)
admin.site.register(PendingReportSubmission, PendingReportSubmissionAdmin)