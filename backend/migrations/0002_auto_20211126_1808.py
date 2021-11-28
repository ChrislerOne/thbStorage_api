# Generated by Django 3.2.9 on 2021-11-26 17:08

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='directorymodel',
            name='directory',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='backend.directorymodel'),
        ),
        migrations.AlterField(
            model_name='filemodel',
            name='last_changed',
            field=models.DateTimeField(default=datetime.datetime(2021, 11, 26, 18, 8, 43, 51932)),
        ),
    ]
