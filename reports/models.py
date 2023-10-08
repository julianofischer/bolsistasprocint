from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver
from datetime import datetime, timedelta


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class Scholarship(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        verbose_name = "Tipo de Bolsa"
        verbose_name_plural = "Tipos de Bolsas"

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        verbose_name = "Função"
        verbose_name_plural = "Funções"

    def __str__(self):
        return self.name


class Eixo(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        verbose_name = "Eixo"
        verbose_name_plural = "Eixos"

    def __str__(self):
        return self.name


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    scholarship = models.ForeignKey(
        Scholarship, on_delete=models.CASCADE, null=True
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True)
    eixo = models.ForeignKey(Eixo, on_delete=models.CASCADE, null=True)
    ch = models.IntegerField(default=0)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"


# Create your models here.
class Report(models.Model):
    
    class Meta:
        verbose_name = "Relatório"
        verbose_name_plural = "Relatórios"

    created_at = models.DateTimeField(auto_now_add=True)
    ref_month = models.DateField()
    user = models.ForeignKey(
        "reports.CustomUser", related_name="reports", on_delete=models.CASCADE
    )

    @property
    def total_hours(self):
        return sum([entry.hours for entry in self.entries.all()], timedelta(0))
    
    @property
    def state(self):
        if self.submissions.exists():
            return self.submissions.last().status
        return "Aberto"
    
    @property
    def last_submission(self):
        if self.submissions.exists():
            return self.submissions.last()
        return None

    def formatted_ref_month(self):
        return self.ref_month.strftime('%m-%Y')
    
    def __str__(self) -> str:
        return f"{self.user} - {self.formatted_ref_month()} ({self.total_hours})"


class ReportEntry(models.Model):
    class Meta:
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"

    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="entries"
    )
    description = models.CharField(max_length=1024)
    date = models.DateField()
    init_hour = models.TimeField()
    end_hour = models.TimeField()

    @property
    def hours(self):
        # Convert TimeField values to datetime.time objects
        init_time = datetime.strptime(str(self.init_hour), '%H:%M:%S').time()
        end_time = datetime.strptime(str(self.end_hour), '%H:%M:%S').time()

        # Calculate the time difference as a timedelta object
        time_difference = timedelta(
            hours=end_time.hour - init_time.hour,
            minutes=end_time.minute - init_time.minute,
            seconds=end_time.second - init_time.second
        )
        return time_difference
    
    def __str__(self) -> str:
        return f"{self.report.user} - {self.date} ({self.hours})"


class ReportSubmission(models.Model):
    class Meta:
        verbose_name = "Relatório entregue"
        verbose_name_plural = "Relatórios entregues"
    class ReportStatus(models.TextChoices):
        PENDING = "Em análise"
        APPROVED = "Aprovado"
        REJECTED = "Rejeitado"

    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="submissions"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        choices=ReportStatus.choices,
        max_length=10,
        default=ReportStatus.PENDING,
    )
    last_status_change = models.DateTimeField(auto_now=True)
    reviewer = models.ForeignKey(
        CustomUser, related_name="submissions", on_delete=models.SET_NULL, null=True
    )
    pdf_file = models.FileField(upload_to="reports")
    reason = models.CharField(max_length=1024, blank=True)

    def __str__(self) -> str:
        return f"{self.report.user} - {self.submitted_at} ({self.status})"


@receiver(pre_save, sender=ReportSubmission)
def update_last_status_change(sender, instance, **kwargs):
    if instance.pk:
        original_submission = ReportSubmission.objects.get(pk=instance.pk)
        if original_submission.status != instance.status:
            instance.last_status_change = timezone.now()



class PendingReportSubmissionsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=ReportSubmission.ReportStatus.PENDING)

class PendingReportSubmission(ReportSubmission):
    manager = PendingReportSubmissionsManager()
    class Meta:
        proxy = True
        verbose_name = "Relatório pendente de análise"
        verbose_name_plural = "Relatórios pendentes de análise"

    