# Generated by Django 4.1.6 on 2023-08-20 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Authentication', '0003_alter_customuser_full_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='phone_number',
        ),
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
