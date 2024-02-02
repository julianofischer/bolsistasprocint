from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from datetime import datetime, timedelta
from phonenumber_field.modelfields import PhoneNumberField


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
    name = models.CharField(max_length=256)

    class Meta:
        verbose_name = "Tipo de Bolsa"
        verbose_name_plural = "Tipos de Bolsas"

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=256)

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
    name = models.CharField(max_length=30, verbose_name="Nome")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    scholarship = models.ForeignKey(
        Scholarship, on_delete=models.CASCADE, null=True, blank=True
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True)
    eixo = models.ForeignKey(Eixo, on_delete=models.CASCADE, null=True, blank=True)
    ch = models.IntegerField(default=0)
    phone_number = PhoneNumberField(null=True, blank=True, region="BR")

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
    def signed(self):
        return self.signatures.exists()
    
    @property
    def is_signed(self):
        return self.signed

    def signed_by_user(self):
        return self.signatures.filter(user=self.user).exists()
    
    def signed_by_staff(self):
        return self.signatures.filter(user__is_staff=True).exclude(user=self.user).exists()

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
        return self.ref_month.strftime("%m-%Y")

    def __str__(self) -> str:
        return f"{self.user} - {self.formatted_ref_month()} ({self.total_hours})"
    
    # only save if it is opened
    # def save(self, *args, **kwargs):
        # 'Report' instance needs to have a primary key value before this relationship can be used.
        # if not self.signed():
            # super().save(*args, **kwargs)
        # raise ValidationError("Relatório está assinado e não pode ser alterado")
    
    def sign(self, user):
        if user==self.user and self.signed_by_user():
            raise ValidationError("Usuário já assinou este relatório")
        if user!=self.user and user.is_staff and self.signed_by_staff():
            raise ValidationError("Gerente já assinou este relatório")
        ReportSignature.objects.create(user=user, report=self)



class ReportEntry(models.Model):
    class Meta:
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="entries")
    description = models.CharField(max_length=1024)
    date = models.DateField()
    init_hour = models.TimeField()
    end_hour = models.TimeField()

    @property
    def hours(self):
        # Convert TimeField values to datetime.time objects
        init_time = datetime.strptime(str(self.init_hour), "%H:%M:%S").time()
        end_time = datetime.strptime(str(self.end_hour), "%H:%M:%S").time()

        # Calculate the time difference as a timedelta object
        time_difference = timedelta(
            hours=end_time.hour - init_time.hour,
            minutes=end_time.minute - init_time.minute,
            seconds=end_time.second - init_time.second,
        )
        return time_difference

    def __str__(self) -> str:
        return f"{self.report.user} - {self.date} ({self.hours})"
    
    # only save if it is opened
    # def save(self, *args, **kwargs):
    #     if not self.report.signed:
    #         super().save(*args, **kwargs)
    #     raise ValidationError("Relatório está assinado e não pode ser alterado")


class ReportSubmission(models.Model):
    class Meta:
        verbose_name = "Relatório entregue"
        verbose_name_plural = "Relatórios entregues"

    class ReportStatus(models.TextChoices):
        PENDING = "Em análise"
        APPROVED = "Aprovado"
        REJECTED = "Rejeitado"
        SIGNED = "Assinado"

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
        return (
            super().get_queryset().filter(status=ReportSubmission.ReportStatus.PENDING)
        )


class PendingReportSubmission(ReportSubmission):
    manager = PendingReportSubmissionsManager()

    class Meta:
        proxy = True
        verbose_name = "Relatório pendente de análise"
        verbose_name_plural = "Relatórios pendentes de análise"


class ReportSignature(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="signatures")
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "report"]
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"

    # a user can only sign his own report and only once
    # is_staff can sign any report but only once
    def save(self, *args, **kwargs):
        if self.user == self.report.user or self.user.is_staff:
            super().save(*args, **kwargs)
        raise ValidationError("Usuário não pode assinar este relatório")