"""
Migration to remove token blacklist tables.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_partner_user'),
    ]

    operations = [
        # Drop token blacklist tables if they exist
        migrations.RunSQL(
            sql="""
                DROP TABLE IF EXISTS token_blacklist_blacklistedtoken CASCADE;
                DROP TABLE IF EXISTS token_blacklist_outstandingtoken CASCADE;
            """,
            reverse_sql="""
                -- No reverse operation needed - tables are being removed
            """,
        ),
    ]
