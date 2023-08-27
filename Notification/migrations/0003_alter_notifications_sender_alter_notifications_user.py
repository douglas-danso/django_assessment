# Generated by Django 4.1.6 on 2023-07-21 18:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Notification', '0002_notifications_notification_type_notifications_sender_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notifications',
            name='sender',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sender_notifications', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='notifications',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reciever_notifications', to=settings.AUTH_USER_MODEL),
        ),
    ]
