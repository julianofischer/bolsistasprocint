from django.shortcuts import render

# Create your views here.
# views.py
from django.shortcuts import render, redirect
from .forms import LoginForm
from django.contrib.auth import authenticate, login


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
