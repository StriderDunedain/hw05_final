# Generated by Django 2.2.16 on 2022-12-20 09:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_post_was_edited'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='was_edited',
        ),
    ]