from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from datetime import datetime, timedelta
from reports.models import Report, ReportSubmission


class Command(BaseCommand):
    help = "Send monthly emails on the last day of the month"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry_run',
            action='store_true',
            help='Run in dry run mode (no actual emails sent)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Check if it's the last day of the month
        today = datetime.now()

        for_current_month = today.month != (today + timedelta(days=1)).month
        if for_current_month:
            report_day = today
        else:
            report_day = today + timedelta(days=-today.day)

        # get all reports from the current month that doens't have a submission in the state of 'pending' or 'approved'
        reports = Report.objects.filter(ref_month__month=report_day.month).exclude(
            submissions__status__in=[
                ReportSubmission.ReportStatus.APPROVED,
                ReportSubmission.ReportStatus.PENDING,
            ]
        )

        template = "Olá, bolsita PROCINT!\nEste é um lembrete automático de que você tem até o dia 5 enviar o relatório mensal do mês de {}."
        subject = "[PROCINT] Lembrete Mensal"
        sender = "julianofischer@gmail.com"
        recipients = ["julianofischer@gmail.com"]
        bcc = [report.user.email for report in reports]
        template = template.format(report_day.strftime("%B"))
        if not dry_run:
            send_mail(
                subject,
                template,
                sender,
                recipients,
                fail_silently=False,
                bcc=bcc,
            )
            self.stdout.write(self.style.SUCCESS("Emails sent successfully."))
        else:
            print(f"Subject: {subject}, Template: {template}, Recipients: {recipients}")
            self.stdout.write(self.style.SUCCESS("[DRY_RUN] Emails sent successfully."))