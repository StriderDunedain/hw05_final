# Generated by Django 2.2.16 on 2022-12-20 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_auto_20221220_1151'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='was_edited',
            field=models.BooleanField(default=False),
        ),
    ]
