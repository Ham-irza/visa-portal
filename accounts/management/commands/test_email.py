"""
Management command to test email sending.
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email sending'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing email configuration...'))
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        # Try to send a test email
        try:
            result = send_mail(
                subject='Test Email from Hainan Builder Portal',
                message='This is a test email to verify SMTP configuration.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['partner@hainancorporateservices.com'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Email sent successfully! Result: {result}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email: {e}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
