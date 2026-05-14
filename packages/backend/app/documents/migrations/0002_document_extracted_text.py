# Generated manually for Step 5.1

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0001_document"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="extracted_text",
            field=models.TextField(blank=True, default=""),
        ),
    ]
