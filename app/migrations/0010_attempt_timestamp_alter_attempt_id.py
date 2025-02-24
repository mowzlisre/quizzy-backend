# Generated by Django 5.1.6 on 2025-02-24 02:56

import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_alter_attempt_answers_alter_attempt_feedback'),
    ]

    operations = [
        migrations.AddField(
            model_name='attempt',
            name='timeStamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='attempt',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
