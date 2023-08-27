# Generated by Django 4.1.6 on 2023-08-26 21:43

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('User_Relationship', '0004_posts_likes_delete_likes'),
    ]

    operations = [
        migrations.AddField(
            model_name='comments',
            name='file',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='comments',
            name='likes',
            field=models.ManyToManyField(related_name='liked_comments', to=settings.AUTH_USER_MODEL),
        ),
    ]