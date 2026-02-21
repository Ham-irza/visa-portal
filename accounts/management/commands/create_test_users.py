"""
Django management command to create test users for Playwright tests.
Run: python manage.py create_test_users
"""
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Partner
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = "Create test users for Playwright E2E tests"

    def handle(self, *args, **options):
        # Test partner credentials (from tests/helpers.ts TEST_CREDENTIALS)
        partner_email = 'partner@hainanbuilder.com'
        partner_password = 'PartnerPassword123!'
        admin_email = 'admin@example.com'
        admin_password = 'AdminPassword123!'

        # Create or update admin user
        try:
            admin_user = User.objects.get(email=admin_email)
            admin_user.set_password(admin_password)
            admin_user.save()
            self.stdout.write(self.style.WARNING(f'✓ Updated admin user: {admin_email}'))
        except User.DoesNotExist:
            try:
                # Try with simple username first
                admin_user = User.objects.create_user(
                    email=admin_email,
                    username=admin_email.split('@')[0],
                    password=admin_password,
                    is_staff=True,
                    is_superuser=True,
                    is_active=True,
                )
                admin_user.role = 'admin'
                admin_user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created admin user: {admin_email}'))
            except IntegrityError:
                # Username exists, use unique one
                admin_user = User.objects.create_user(
                    email=admin_email,
                    username=f'admin_{uuid.uuid4().hex[:8]}',
                    password=admin_password,
                    is_staff=True,
                    is_superuser=True,
                    is_active=True,
                )
                admin_user.role = 'admin'
                admin_user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created admin user: {admin_email}'))

        # Create or update partner user with approved status
        try:
            partner_user = User.objects.get(email=partner_email)
            partner_user.set_password(partner_password)
            partner_user.save()
            self.stdout.write(self.style.WARNING(f'✓ Updated partner user: {partner_email}'))
        except User.DoesNotExist:
            try:
                partner_user = User.objects.create_user(
                    email=partner_email,
                    username=partner_email.split('@')[0],
                    password=partner_password,
                    is_staff=False,
                    is_superuser=False,
                    is_active=True,
                )
                partner_user.role = 'partner'
                partner_user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created partner user: {partner_email}'))
            except IntegrityError:
                # Username exists, use unique one
                partner_user = User.objects.create_user(
                    email=partner_email,
                    username=f'partner_{uuid.uuid4().hex[:8]}',
                    password=partner_password,
                    is_staff=False,
                    is_superuser=False,
                    is_active=True,
                )
                partner_user.role = 'partner'
                partner_user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created partner user: {partner_email}'))

        # Create or update partner profile with APPROVED status (so tests can login)
        try:
            partner = Partner.objects.get(user=partner_user)
            partner.status = Partner.STATUS_APPROVED
            partner.save()
            self.stdout.write(self.style.WARNING(f'✓ Updated partner profile: {partner.company_name}'))
        except Partner.DoesNotExist:
            partner = Partner.objects.create(
                user=partner_user,
                company_name='Test Partner Company',
                contact_name='Test Partner',
                contact_phone='+86 138 0000 0000',
                status=Partner.STATUS_APPROVED,  # IMPORTANT: Must be approved to login
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created partner profile: {partner.company_name}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Test users created successfully!'))
        self.stdout.write(self.style.WARNING(f'\nTest Credentials:'))
        self.stdout.write(f'  Admin: {admin_email} / {admin_password}')
        self.stdout.write(f'  Partner: {partner_email} / {partner_password}')


