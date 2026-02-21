# Generated migration to add ServiceType and RequiredDocument models and seed initial data
from django.db import migrations, models
import django.db.models.deletion


def create_initial(apps, schema_editor):
    ServiceType = apps.get_model('documents', 'ServiceType')
    RequiredDocument = apps.get_model('documents', 'RequiredDocument')

    services = [
        ('business_registration', 'Business Registration', ''),
        ('work_permit_z', 'Work Permit (Z Visa)', ''),
        ('m_visa', 'M Visa', ''),
        ('tourist_group', 'Tourist Group Visa', ''),
        ('health_tour', 'Health Tour Visa', ''),
        ('family_visa', 'Family Visa', ''),
    ]

    created = {}
    for key, name, desc in services:
        created[key] = ServiceType.objects.create(key=key, name=name, description=desc)

    # Business Registration
    br = created['business_registration']
    br_items = [
        ('Company 3 name suggestions', False),
        ('Shareholder Information', False),
        ('Email', False),
        ('Phone number', False),
        ('Passport bio page', False),
        ('Passport signature page (optional)', True),
        ('China Last Entry Page (optional)', True),
        ('China or Other Country Address', False),
        ('Business Scope in Short', False),
    ]
    for i, (t, opt) in enumerate(br_items):
        RequiredDocument.objects.create(service=br, title=t, optional=opt, order=i)

    # Work Permit (Z Visa)
    z = created['work_permit_z']
    z_items = [
        ('White background photo', False),
        ('Degree Certificate or Transcript', False),
        ('Medical File', False),
        ('Police Non-Criminal Certificate', False),
        ('Experience letter', False),
        ('Any professional Certificate (optional)', True),
        ('Language Certificate (Chinese or other) (optional)', True),
        ('Any additional certificate (optional)', True),
    ]
    for i, (t, opt) in enumerate(z_items):
        RequiredDocument.objects.create(service=z, title=t, optional=opt, order=i)

    # M Visa
    m = created['m_visa']
    m_items = [
        ('Passport bio page', False),
        ('White background photo', False),
        ('Non criminal certificate', False),
        ('Hotel booking', False),
        ('Flight booking', False),
        ('Itinerary', False),
        ('Email', False),
        ('Phone number', False),
        ('Incorporation letter (if any)', True),
        ('Information sheet filling', False),
        ('China last entry page (optional)', True),
    ]
    for i, (t, opt) in enumerate(m_items):
        RequiredDocument.objects.create(service=m, title=t, optional=opt, order=i)

    # Tourist Group Visa
    tg = created['tourist_group']
    tg_items = [
        ('Passport bio page', False),
        ('Passport signature page (if any)', True),
        ('White background photo', False),
        ('Police non criminal certificate (optional)', True),
        ('China last entry page (optional)', True),
    ]
    for i, (t, opt) in enumerate(tg_items):
        RequiredDocument.objects.create(service=tg, title=t, optional=opt, order=i)

    # Health Tour Visa
    ht = created['health_tour']
    ht_items = [
        ('All M Visa documents', False),
        ('Previous health reports history and documents proof', False),
    ]
    for i, (t, opt) in enumerate(ht_items):
        RequiredDocument.objects.create(service=ht, title=t, optional=opt, order=i)

    # Family Visa
    fv = created['family_visa']
    fv_items = [
        ('Z Visa documents (as above)', False),
        ('Children Passport(s)', False),
        ('Child Passport bio page photo', False),
        ('White background photo', False),
        ('Marriage certificate', False),
        ('Birth certificate', False),
    ]
    for i, (t, opt) in enumerate(fv_items):
        RequiredDocument.objects.create(service=fv, title=t, optional=opt, order=i)


def reverse_initial(apps, schema_editor):
    ServiceType = apps.get_model('documents', 'ServiceType')
    keys = ['business_registration', 'work_permit_z', 'm_visa', 'tourist_group', 'health_tour', 'family_visa']
    ServiceType.objects.filter(key__in=keys).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.SlugField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
            ],
            options={'db_table': 'service_types', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='RequiredDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('optional', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requirements', to='documents.servicetype')),
            ],
            options={'db_table': 'service_required_documents', 'ordering': ['service_id', 'order']},
        ),
        migrations.RunPython(create_initial, reverse_initial),
    ]
