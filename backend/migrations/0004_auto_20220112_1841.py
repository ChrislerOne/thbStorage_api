# Generated by Django 3.2.9 on 2022-01-12 17:41

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0003_auto_20211215_0840'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='filemodel',
            name='directory',
        ),
        migrations.RemoveField(
            model_name='filemodel',
            name='owner',
        ),
        migrations.AlterField(
            model_name='customuidmodel',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='filenewmodel',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='filenewmodel',
            name='last_changed',
            field=models.DateTimeField(default=datetime.datetime(2022, 1, 12, 17, 41, 42, 484383, tzinfo=utc)),
        ),
        migrations.DeleteModel(
            name='DirectoryModel',
        ),
        migrations.DeleteModel(
            name='FileModel',
        ),
    ]
