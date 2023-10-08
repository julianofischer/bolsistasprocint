from django.db.models.signals import post_save
from django.dispatch import receiver
from reports.email import send_mail
from django.conf import settings
from .models import ReportSubmission  # Replace with your actual model import

@receiver(post_save, sender=ReportSubmission)
def send_email_on_report_submission_creation(sender, instance, created, **kwargs):
    if created:
        recipient = instance.report.user.email
        subject = 'New Report Submission Created'
        message = 'A new report submission has been created.'
        recipient_list = [recipient]  # Replace with the recipient's email address
        try:
            send_mail(subject, message, recipient_list)
        except Exception as e:
            print(e)
