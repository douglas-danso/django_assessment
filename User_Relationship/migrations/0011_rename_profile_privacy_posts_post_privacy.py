# Generated by Django 4.1.6 on 2023-08-27 15:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('User_Relationship', '0010_posts_profile_privacy'),
    ]

    operations = [
        migrations.RenameField(
            model_name='posts',
            old_name='profile_privacy',
            new_name='post_privacy',
        ),
    ]