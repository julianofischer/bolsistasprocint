from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver


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


class Role(models.Model):
    name = models.CharField(max_length=30)


class Eixo(models.Model):
    name = models.CharField(max_length=30)


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


# Create your models here.
class Report(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    ref_month = models.DateField()
    user = models.ForeignKey(
        "reports.CustomUser", related_name="reports", on_delete=models.CASCADE
    )

    @property
    def total_hours(self):
        return sum([entry.hours for entry in self.entries.all()])


class ReportEntry(models.Model):
    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="entries"
    )
    description = models.CharField(max_length=1024)
    date = models.DateField()
    init_hour = models.TimeField()
    end_hour = models.TimeField()

    @property
    def hours(self):
        return self.end_hour.hour - self.init_hour.hour


class ReportSubmission(models.Model):
    class ReportStatus(models.TextChoices):
        PENDING = "pendente"
        APPROVED = "aprovado"
        REJECTED = "rejeitado"

    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="submission"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        choices=ReportStatus.choices,
        max_length=10,
        default=ReportStatus.PENDING,
    )
    last_status_change = models.DateTimeField(auto_now=True)
    reviewer = models.ForeignKey(
        CustomUser, related_name="submissions", on_delete=models.CASCADE
    )
    pdf_file = models.FileField(upload_to="reports")
    reason = models.CharField(max_length=1024, blank=True)


@receiver(pre_save, sender=ReportSubmission)
def update_last_status_change(sender, instance, **kwargs):
    if instance.pk:
        original_submission = ReportSubmission.objects.get(pk=instance.pk)
        if original_submission.status != instance.status:
            instance.last_status_change = timezone.now()
