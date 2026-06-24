from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0006_billing_type_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="payment_url",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
