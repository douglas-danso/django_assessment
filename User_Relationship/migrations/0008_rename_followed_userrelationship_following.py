# Generated by Django 4.1.6 on 2023-08-27 01:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('User_Relationship', '0007_posts_original_post'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userrelationship',
            old_name='followed',
            new_name='following',
        ),
    ]