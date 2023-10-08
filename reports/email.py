from django.core.mail import send_mass_mail, EmailMessage
from django.conf import settings


def send_mail(subject, message, recipients, bcc=None):
    message = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.EMAIL_HOST_USER,
        to=recipients,
        bcc=bcc,
    )
    message.send()
