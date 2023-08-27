# Generated by Django 4.1.6 on 2023-08-27 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User_Relationship', '0009_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='posts',
            name='profile_privacy',
            field=models.CharField(choices=[('public', 'Public'), ('followers', 'Followers'), ('private', 'Private')], default='public', max_length=10),
        ),
    ]
