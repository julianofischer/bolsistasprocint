# forms.py
from django import forms
from .models import ReportEntry


class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

class ReportEntryForm(forms.ModelForm):
    class Meta:
        model = ReportEntry
        fields = ['description', 'date', 'init_hour', 'end_hour']