# Generated by Django 4.1.6 on 2023-08-25 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Authentication', '0005_customuser_profile_picture_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='bio',
            field=models.TextField(blank=True, null=True),
        ),
    ]