# Generated by Django 3.2.9 on 2021-12-01 21:23

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filemodel',
            name='last_changed',
            field=models.DateTimeField(default=datetime.datetime(2021, 12, 1, 21, 23, 5, 451589, tzinfo=utc)),
        ),
    ]
