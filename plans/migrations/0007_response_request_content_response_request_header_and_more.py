# Generated by Django 4.2.1 on 2023-07-15 21:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0006_alter_templateversion_header"),
    ]

    operations = [
        migrations.AddField(
            model_name="response",
            name="request_content",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="response",
            name="request_header",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="response",
            name="request_system_message",
            field=models.TextField(blank=True, null=True),
        ),
    ]
