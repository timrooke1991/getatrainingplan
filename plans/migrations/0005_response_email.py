# Generated by Django 4.2.1 on 2023-07-09 17:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0004_templateversion_token_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="response",
            name="email",
            field=models.EmailField(blank=True, max_length=255, null=True),
        ),
    ]
