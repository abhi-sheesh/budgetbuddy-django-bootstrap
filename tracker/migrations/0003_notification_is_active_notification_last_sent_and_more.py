# Generated by Django 5.2.1 on 2025-05-28 06:12

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_bill_notification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='last_sent',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notification',
            name='repeat_frequency',
            field=models.CharField(choices=[('ONCE', 'Once'), ('DAILY', 'Daily'), ('WEEKLY', 'Weekly')], default='ONCE', max_length=10),
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('budget_alerts', models.BooleanField(default=True)),
                ('goal_alerts', models.BooleanField(default=True)),
                ('bill_reminders', models.BooleanField(default=True)),
                ('budget_threshold', models.IntegerField(default=90)),
                ('goal_days_prior', models.IntegerField(default=7)),
                ('bill_days_prior', models.IntegerField(default=3)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
