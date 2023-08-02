# myproject/urls.py
from django.contrib import admin
from django.urls import path, include
from reports.views import login_view

urlpatterns = [
    path("login/", login_view, name="login"),
    path("admin/", admin.site.urls),
    path("api/v1", include("reports.urls")),
]
