# Generated by Django 4.2 on 2024-07-22 11:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_userprofile_created_at_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='file_text',
        ),
    ]
