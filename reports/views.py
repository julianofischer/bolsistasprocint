from typing import Any, Dict
from django.db import models
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.contrib import messages

# Create your views here.
# views.py
from django.shortcuts import render, redirect
from .forms import LoginForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from .models import Report, ReportEntry
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
    DetailView,
)
from django.urls import reverse_lazy, reverse
from datetime import datetime, timedelta


class CustomLoginView(LoginView):
    template_name = "reports/login.html"  # Specify your custom login template
    success_url = reverse_lazy(
        "/relatorios"
    )  # Replace 'home' with your desired redirect URL


def inserir_relatorio_view(request):
    user = request.user
    context = {
        "user": user,
    }
    print(user)
    return render(request, "reports/inserir_report.html", context)


class UserReportsListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = "reports/user_reports.html"
    context_object_name = "reports"

    def get_queryset(self):
        # Get the currently logged-in user
        user = self.request.user

        # Query all reports related to the user
        return Report.objects.filter(user=user).order_by("-ref_month")


class ReportEntriesListView(LoginRequiredMixin, ListView):
    model = ReportEntry
    template_name = "reports/report_entries.html"
    context_object_name = "entries"

    def get(self, request, *args: str, **kwargs: Any):
        report_id = self.kwargs.get("report_id")
        existing_submissions = ReportSubmission.objects.filter(
            report_id=report_id,
            status__in=[
                ReportSubmission.ReportStatus.PENDING,
                ReportSubmission.ReportStatus.APPROVED,
            ],
        )

        if existing_submissions.exists():
            messages.error(
                request, "Nao e possivel abrir relatorio enviado para analise."
            )
            return redirect(reverse("user-reports"))
        else:
            return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        report_id = self.kwargs["report_id"]
        # Query all entries related to the report
        return ReportEntry.objects.filter(report__id=report_id)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        data = super().get_context_data(**kwargs)
        display_entry = ReportEntry.objects.filter(
            report__id=self.kwargs["report_id"]
        ).last()
        if display_entry:
            data["display_entry"] = display_entry
        else:
            display_entry = ReportEntry()
            display_entry.description = ""
            display_entry.date = datetime.now() - timedelta(days=1)
            data["display_entry"] = display_entry


        data["report_id"] = self.kwargs["report_id"]
        data["edit_mode"] = self.kwargs.get("edit_mode", False)
        data["total_hours"] = Report.objects.get(
            id=self.kwargs["report_id"]
        ).total_hours
        return data


class ReportEntryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ReportEntry
    fields = ["description", "date", "init_hour", "end_hour"]
    template_name = "reports/report_entries.html"
    success_message = "Entrada criada com sucesso!"

    def form_valid(self, form):
        form.instance.report_id = self.kwargs["report_id"]
        return super().form_valid(form)

    def get_success_url(self):
        # Define the URL where you want to redirect after a successful form submission
        return reverse_lazy(
            "report-entries", kwargs={"report_id": self.kwargs["report_id"]}
        )


# PARECIDA COM A DE CIMA, EDITANDO UMA ENTRY
class ReportEntryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ReportEntry
    fields = ["description", "date", "init_hour", "end_hour"]
    template_name = "reports/report_entries.html"
    context_object_name = "entry"
    success_message = "Entrada editada com sucesso!"

    def get_queryset(self) -> QuerySet[Any]:
        report_id = self.kwargs["report_id"]
        # Query all entries related to the report
        return ReportEntry.objects.filter(report__id=report_id)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        data = super().get_context_data(**kwargs)
        data["display_entry"] = ReportEntry.objects.get(id=self.kwargs["pk"])
        data["report_id"] = self.kwargs["report_id"]
        data["entry_id"] = self.kwargs["pk"]
        data["edit_mode"] = True
        data["entries"] = ReportEntry.objects.filter(
            report__id=self.kwargs["report_id"]
        )
        data["total_hours"] = Report.objects.get(
            id=self.kwargs["report_id"]
        ).total_hours
        return data

    def get_success_url(self):
        # Define the URL where you want to redirect after a successful form submission
        return reverse_lazy(
            "report-entries", kwargs={"report_id": self.kwargs["report_id"]}
        )


class ReportEntryDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = ReportEntry
    success_message = "Entrada deletada com sucesso!"

    def get_success_url(self):
        # Define the URL where you want to redirect after a successful form submission
        return reverse_lazy(
            "report-entries", kwargs={"report_id": self.kwargs["report_id"]}
        )


from .pdf import generate_pdf
from django.http import HttpRequest, HttpResponse


class PDFView(View):
    def get(self, request, *args, **kwargs):
        report_id = self.kwargs.get("report_id")
        existing_submissions = ReportSubmission.objects.filter(
            report_id=report_id,
            status__in=[
                ReportSubmission.ReportStatus.PENDING,
                ReportSubmission.ReportStatus.APPROVED,
            ],
        )

        if existing_submissions.exists():
            messages.error(
                request, "Nao e possivel imprimir relatorio enviado para analise."
            )
            return redirect(reverse("user-reports"))

        header_data = {}
        report_id = self.kwargs["report_id"]
        report = Report.objects.get(id=report_id)

        header_data["bolsista"] = report.user.name
        header_data["funcao"] = report.user.role
        header_data["periodo"] = report.formatted_ref_month()
        header_data["telefone_institucional"] = ""
        header_data["email"] = report.user.email

        row_data = []
        entries = ReportEntry.objects.filter(report__id=report_id)
        for entry in entries:
            row_data.append(
                {
                    "dia": entry.date.day,
                    "atividade": entry.description,
                    "inicio": entry.init_hour,
                    "fim": entry.end_hour,
                    "ch": entry.hours,
                }
            )

        pdf_file = generate_pdf(header_data, row_data)
        response = HttpResponse(content_type="application/pdf")
        filename = f"{report.user.name} - {report.ref_month.strftime('%B')} - {report.ref_month.year}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write(pdf_file)
        return response


from django.views.generic.edit import CreateView
from .models import ReportSubmission
from .forms import ReportSubmissionForm


class ReportSubmissionCreateView(CreateView):
    model = ReportSubmission
    form_class = ReportSubmissionForm
    template_name = "reports/report_submission.html"
    success_url = "/success/"  # Replace with the actual success URL

    def form_valid(self, form):
        # Check if there are any existing pending or approved submissions
        report_id = self.kwargs.get("report_id")
        form.instance.report_id = report_id
        existing_submissions = ReportSubmission.objects.filter(
            report_id=report_id,
            status__in=[
                ReportSubmission.ReportStatus.PENDING,
                ReportSubmission.ReportStatus.APPROVED,
            ],
        )

        if existing_submissions.exists():
            # If there are existing pending or approved submissions, reject the new submission
            messages.error(
                self.request,
                "Já existe uma submissão pendente ou aprovada para este relatório.",
            )
        return super().form_valid(form)

    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        report_id = self.kwargs.get("report_id")
        existing_submissions = ReportSubmission.objects.filter(
            report_id=report_id,
            status__in=[
                ReportSubmission.ReportStatus.PENDING,
                ReportSubmission.ReportStatus.APPROVED,
            ],
        )

        if existing_submissions.exists():
            messages.error(
                request,
                "Já existe uma submissão pendente ou aprovada para este relatório.",
            )
            return redirect(reverse("user-reports"))
        else:
            return super().get(request, *args, **kwargs)


class ReportSubmissionDetailView(LoginRequiredMixin, DetailView):
    model = ReportSubmission
    template_name = "reports/report_submission_details.html"
    context_object_name = "report_submission"


def create_report(request):
    if request.method == 'POST':
        # check if a report for current month already exists
        report = Report.objects.filter(user=request.user, ref_month__year=datetime.now().year, ref_month__month=datetime.now().month)
        if not report:
            # Create a new Report instance with default values
            now = datetime.now()
            report = Report.objects.create(ref_month=now, user=request.user)  # Modify this to set default values as needed
            messages.success(request, "Relatorio criado com sucesso!")
        else:
            messages.error(request, "Relatorio ja existe para este mes!")
    else:
        messages.error(request, "Metodo nao permitido!")
    
    return redirect('user-reports') 
