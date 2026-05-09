"""
Migration: add token_count field to AIPrediction for telemetry tracking
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hospital", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiprediction",
            name="token_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
