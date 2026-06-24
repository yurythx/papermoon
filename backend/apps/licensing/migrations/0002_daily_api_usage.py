from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("customers", "0004_add_asaas_customer_id"),
        ("licensing", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyApiUsage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="daily_api_usage",
                        to="customers.customer",
                    ),
                ),
                ("date", models.DateField(default=django.utils.timezone.now)),
                ("calls_count", models.IntegerField(default=0)),
            ],
            options={
                "db_table": "licensing_daily_api_usage",
                "ordering": ["date"],
            },
        ),
        migrations.AddConstraint(
            model_name="dailyapiusage",
            constraint=models.UniqueConstraint(
                fields=["customer", "date"], name="uq_daily_api_usage_customer_date"
            ),
        ),
        migrations.AddIndex(
            model_name="dailyapiusage",
            index=models.Index(
                fields=["customer", "date"], name="licensing_daily_api_customer_date_idx"
            ),
        ),
    ]
