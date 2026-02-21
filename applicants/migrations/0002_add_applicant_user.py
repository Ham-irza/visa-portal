# Generated migration: add nullable partner and applicant_user to Applicant
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('applicants', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicant',
            name='partner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='applicants', to='accounts.partner'),
        ),
        migrations.AddField(
            model_name='applicant',
            name='applicant_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='applicant_profiles', to=settings.AUTH_USER_MODEL),
        ),
    ]
