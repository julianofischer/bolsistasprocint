from typing import Any, Dict
from django.db import models
from django.db.models.query import QuerySet
from django.shortcuts import render

# Create your views here.
# views.py
from django.shortcuts import render, redirect
from .forms import LoginForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from .models import Report, ReportEntry
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a protected page after successful login
                return redirect("protected_page_url_name")
            else:
                form.add_error(None, "Senha ou email inválido.")
    else:
        form = LoginForm()

    return render(request, "reports/login.html", {"form": form})


def inserir_relatorio_view(request):
    user = request.user
    context = {
        "user": user,
    }
    print(user)
    return render(request, "reports/inserir_report.html", context)


class UserReportsListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'reports/user_reports.html'
    context_object_name = 'reports'

    def get_queryset(self):
        # Get the currently logged-in user
        user = self.request.user

        # Query all reports related to the user
        return Report.objects.filter(user=user)


class ReportEntriesListView(LoginRequiredMixin, ListView):
    model = ReportEntry
    template_name = 'reports/report_entries.html'
    context_object_name = 'entries'

    def get_queryset(self) -> QuerySet[Any]:
        report_id = self.kwargs['report_id']
        # Query all entries related to the report
        return ReportEntry.objects.filter(report__id=report_id)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        data = super().get_context_data(**kwargs)
        data["display_entry"] = ReportEntry.objects.filter(report__id=self.kwargs['report_id']).last()
        data["report_id"] = self.kwargs['report_id']
        data["edit_mode"] = self.kwargs.get('edit_mode', False)
        data["total_hours"] = Report.objects.get(id=self.kwargs['report_id']).total_hours
        return data
    

class ReportEntryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ReportEntry
    fields = ['description', 'date', 'init_hour', 'end_hour']
    template_name = 'reports/report_entries.html'
    success_message = "Entrada criada com sucesso!"

    def form_valid(self, form):
        form.instance.report_id = self.kwargs['report_id']
        return super().form_valid(form)
    
    def get_success_url(self):
        # Define the URL where you want to redirect after a successful form submission
        return reverse_lazy('report-entries', kwargs={'report_id': self.kwargs['report_id']})
    

# PARECIDA COM A DE CIMA, EDITANDO UMA ENTRY
class ReportEntryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ReportEntry
    fields = ['description', 'date', 'init_hour', 'end_hour']
    template_name = 'reports/report_entries.html'
    context_object_name = 'entry'
    success_message = "Entrada editada com sucesso!"

    def get_queryset(self) -> QuerySet[Any]:
        report_id = self.kwargs['report_id']
        # Query all entries related to the report
        return ReportEntry.objects.filter(report__id=report_id)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        data = super().get_context_data(**kwargs)
        data["display_entry"] = ReportEntry.objects.get(id=self.kwargs["pk"])
        data["report_id"] = self.kwargs['report_id']
        data["entry_id"] = self.kwargs["pk"]
        data["edit_mode"] = True
        data["entries"] = ReportEntry.objects.filter(report__id=self.kwargs['report_id'])
        data["total_hours"] = Report.objects.get(id=self.kwargs['report_id']).total_hours
        return data

    def get_success_url(self):
        # Define the URL where you want to redirect after a successful form submission
        return reverse_lazy('report-entries', kwargs={'report_id': self.kwargs['report_id']})


class ReportEntryDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = ReportEntry
    success_message = "Entrada deletada com sucesso!"

    def get_success_url(self):
        # Define the URL where you want to redirect after a successful form submission
        return reverse_lazy('report-entries', kwargs={'report_id': self.kwargs['report_id']})
