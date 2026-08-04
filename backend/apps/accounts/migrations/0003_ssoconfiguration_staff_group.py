from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_ssoconfiguration"),
    ]

    operations = [
        migrations.AddField(
            model_name="ssoconfiguration",
            name="staff_group",
            field=models.CharField(max_length=255, blank=True, default=""),
        ),
    ]
