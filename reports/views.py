from typing import Any, Dict
from django.db.models.query import QuerySet
from django.shortcuts import render

# Create your views here.
# views.py
from django.shortcuts import render, redirect
from .forms import LoginForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Report, ReportEntry
from django.views.generic import ListView, CreateView, UpdateView
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
        data["last_entry"] = ReportEntry.objects.filter(report__id=self.kwargs['report_id']).last()
        data["report_id"] = self.kwargs['report_id']
        return data
    

class ReportEntryCreateView(LoginRequiredMixin, CreateView):
    model = ReportEntry
    fields = ['description', 'date', 'init_hour', 'end_hour']
    template_name = 'reports/report_entries.html'

    def form_valid(self, form):
        form.instance.report_id = self.kwargs['report_id']
        return super().form_valid(form)
    
    def get_success_url(self):
        # Define the URL where you want to redirect after a successful form submission
        return reverse_lazy('report-entries', kwargs={'report_id': self.kwargs['report_id']})
    

class ReportEntryUpdateView(LoginRequiredMixin, UpdateView):
    model = ReportEntry
    fields = ['description', 'date', 'init_hour', 'end_hour']
    template_name = 'reports/create_update_report_entry.html'

    


