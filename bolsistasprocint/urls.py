# myproject/urls.py
from django.contrib import admin
from django.urls import path, include
from reports.views import login_view, inserir_relatorio_view

urlpatterns = [
    path("login/", login_view, name="login"),
    path(
        "inserir-relatorio/", inserir_relatorio_view, name="inserir-relatorio"
    ),
    path("admin/", admin.site.urls),
    path("api/v1", include("reports.urls")),
]
