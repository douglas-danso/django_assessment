# Generated by Django 4.1.6 on 2023-08-27 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Authentication', '0006_customuser_bio'),
    ]

    operations = [
        migrations.CreateModel(
            name='Privacy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AddField(
            model_name='customuser',
            name='profile_privacy',
            field=models.CharField(choices=[('public', 'Public'), ('followers', 'Followers'), ('private', 'Private')], default='public', max_length=10),
        ),
    ]