# Generated by Django 4.1.6 on 2023-08-27 13:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Authentication', '0007_privacy_customuser_profile_privacy'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Privacy',
        ),
    ]
