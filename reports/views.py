from typing import Any, Dict
from django.contrib.auth.forms import AuthenticationForm
from django.db.models.query import QuerySet
from django.forms.forms import BaseForm
from django.shortcuts import render, get_object_or_404
from django.contrib import messages

# Create your views here.
# views.py
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from .models import Report, ReportEntry, CustomUser
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

    # if user is already logged in, redirect to user-reports
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("user-reports")
        return super().get(request, *args, **kwargs)

    def form_invalid(self, form):
        # check if user exists and is active
        email = form.cleaned_data.get("username")
        # get custom user class
        user = CustomUser.objects.filter(email=email).first()
        if user and not user.is_active:
            messages.error(self.request, "Usuário não está ativo.")
            form.add_error("username", "Usuário não está ativo.")
            form.non_field_errors = None
            self.render_to_response(self.get_context_data(form=form))
        return super().form_invalid(form)


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
                request, "Não é possível abrir relatório enviado para análise."
            )
            return redirect(reverse("user-reports"))
        else:
            return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        report_id = self.kwargs["report_id"]
        user = self.request.user
        # Query all entries related to the report and the user
        # if the report doesn't belong to the user, raise an 404 error
        report = get_object_or_404(Report, id=report_id, user=user)
        return report.entries.all().order_by("-date")

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
        validated = True

        # add entry only if report belongs to the user
        report = Report.objects.get(id=self.kwargs["report_id"])
        if report.user != self.request.user:
            validated = False
            messages.error(
                self.request,
                "Não é possível adicionar entrada a um relatório que não pertence ao usuário.",
            )

        # init_hour must be before end_hour
        if form.instance.init_hour > form.instance.end_hour:
            validated = False
            messages.error(
                self.request,
                "A hora de início deve ser anterior à hora de término.",
            )

        # date must be in the same month as the report
        report = Report.objects.get(id=self.kwargs["report_id"])
        if (
            form.instance.date.month != report.ref_month.month
            or form.instance.date.year != report.ref_month.year
        ):
            validated = False
            messages.error(
                self.request,
                "A data da atividade deve estar no mesmo mês do relatório.",
            )
        if validated:
            return super().form_valid(form)
        else:
            return redirect(
                reverse_lazy(
                    "report-entries", kwargs={"report_id": self.kwargs["report_id"]}
                )
            )

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
        user = self.request.user
        # Query all entries related to the report and the user
        # if the report doesn't belong to the user, raise an 404 error
        report = get_object_or_404(Report, id=report_id, user=user)
        return report.entries.all().order_by("-date")

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

    def form_valid(self, form):
        form.instance.report_id = self.kwargs["report_id"]
        validated = True

        # add entry only if report belongs to the user
        report = Report.objects.get(id=self.kwargs["report_id"])
        if report.user != self.request.user:
            validated = False
            messages.error(
                self.request,
                "Não é possível adicionar entrada a um relatório que não pertence ao usuário.",
            )

        # init_hour must be before end_hour
        if form.instance.init_hour > form.instance.end_hour:
            validated = False
            messages.error(
                self.request,
                "A hora de início deve ser anterior à hora de término.",
            )

        # date must be in the same month as the report
        report = Report.objects.get(id=self.kwargs["report_id"])
        if (
            form.instance.date.month != report.ref_month.month
            or form.instance.date.year != report.ref_month.year
        ):
            validated = False
            messages.error(
                self.request,
                "A data da atividade deve estar no mesmo mês do relatório.",
            )
        if validated:
            return super().form_valid(form)
        else:
            return redirect(
                reverse_lazy(
                    "report-entries", kwargs={"report_id": self.kwargs["report_id"]}
                )
            )


class ReportEntryDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = ReportEntry
    success_message = "Entrada deletada com sucesso!"

    def get_object(self, queryset=None):
        # Get the report entry based on the provided report_id and entry_id
        report_id = self.kwargs["report_id"]
        report = get_object_or_404(Report, pk=report_id, user=self.request.user)
        entry_id = self.kwargs["pk"]
        entry = get_object_or_404(ReportEntry, pk=entry_id, report__id=report_id)
        return entry

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

        # check if report belongs to the user
        report = get_object_or_404(Report, id=report_id, user=request.user)
        existing_submissions = report.submissions.filter(
            status__in=[
                ReportSubmission.ReportStatus.PENDING,
                ReportSubmission.ReportStatus.APPROVED,
            ],
        )

        if existing_submissions.exists():
            messages.error(
                request, "Não é possível imprimir relatório enviado para análise."
            )
            return redirect(reverse("user-reports"))

        header_data = {}
        report_id = self.kwargs["report_id"]
        report = Report.objects.get(id=report_id)

        header_data["bolsista"] = report.user.name
        header_data["funcao"] = report.user.role
        header_data["periodo"] = report.formatted_ref_month()
        header_data["telefone"] = report.user.phone_number or ""
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
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        response.write(pdf_file)
        return response


from django.views.generic.edit import CreateView
from .models import ReportSubmission
from .forms import ReportSubmissionForm


class ReportSubmissionCreateView(CreateView):
    model = ReportSubmission
    form_class = ReportSubmissionForm
    template_name = "reports/report_submission.html"
    success_url = reverse_lazy("user-reports")

    def form_valid(self, form):
        # Check if there are any existing pending or approved submissions
        report_id = self.kwargs.get("report_id")
        report = get_object_or_404(Report, id=report_id, user=self.request.user)
        form.instance.report_id = report_id
        existing_submissions = report.submissions.filter(
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
        else:
            messages.success(
                self.request, "Relatório submetido para aprovação com sucesso!"
            )
        return super().form_valid(form)

    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        report_id = self.kwargs.get("report_id")
        report = get_object_or_404(Report, id=report_id, user=self.request.user)
        existing_submissions = report.submissions.filter(
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

    def get_queryset(self) -> QuerySet[Any]:
        # check if the report belongs to the user
        report_id = self.kwargs.get("report_id")
        report = get_object_or_404(Report, id=report_id, user=self.request.user)
        return report.submissions.all()


def create_report(request):
    if request.method == "POST":
        # check if a report for current month already exists
        report = Report.objects.filter(
            user=request.user,
            ref_month__year=datetime.now().year,
            ref_month__month=datetime.now().month,
        )
        if not report:
            # Create a new Report instance with default values
            now = datetime.now()
            report = Report.objects.create(
                ref_month=now, user=request.user
            )  # Modify this to set default values as needed
            messages.success(request, "Relatório criado com sucesso!")
        else:
            messages.error(request, "Relatório já existe para o mês selecionado!")
    else:
        messages.error(request, "Método nao permitido!")

    return redirect("user-reports")


def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Set user as inactive until email confirmation
            user.save()
            # You can send an email with a confirmation link here
            # After email confirmation, set user.is_active = True and save
            # Send the confirmation email here
            login(request, user)  # Log in the user
            return redirect("user-reports")  # Redirect to a profile or home page
    else:
        form = CustomUserCreationForm()
    return render(request, "reports/register.html", {"form": form})
