# myproject/urls.py
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from django.views.generic import RedirectView
from reports.views import inserir_relatorio_view, CustomLoginView, register_view


urlpatterns = [
    path("", RedirectView.as_view(url="/relatorios/")),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path(
        "inserir-relatorio/", inserir_relatorio_view, name="inserir-relatorio"
    ),
    path("admin/", admin.site.urls),
    path('cadastrar/', register_view, name='register'),
    path("relatorios/", include("reports.urls")),
]
