# Generated by Django 3.1.7 on 2021-12-15 07:40

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('backend', '0002_alter_filemodel_last_changed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuidmodel',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='directorymodel',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='filemodel',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='filemodel',
            name='last_changed',
            field=models.DateTimeField(default=datetime.datetime(2021, 12, 15, 7, 40, 19, 623978, tzinfo=utc)),
        ),
        migrations.CreateModel(
            name='FileNewModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fileName', models.CharField(max_length=500)),
                ('location', models.CharField(blank=True, default='', max_length=500, null=True)),
                ('content', models.FileField(upload_to='')),
                ('checksum', models.CharField(max_length=64, null=True)),
                ('last_changed', models.DateTimeField(default=datetime.datetime(2021, 12, 15, 7, 40, 19, 624978, tzinfo=utc))),
                ('isPublic', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
