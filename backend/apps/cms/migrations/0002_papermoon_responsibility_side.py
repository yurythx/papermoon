from django.db import migrations, models


def forward_side_to_papermoon(apps, schema_editor):
    ServiceResponsibility = apps.get_model("cms", "ServiceResponsibility")
    ServiceResponsibility.objects.filter(side="riissen").update(side="papermoon")


def backward_side_to_riissen(apps, schema_editor):
    ServiceResponsibility = apps.get_model("cms", "ServiceResponsibility")
    ServiceResponsibility.objects.filter(side="papermoon").update(side="riissen")


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forward_side_to_papermoon, backward_side_to_riissen),
        migrations.AlterField(
            model_name="serviceresponsibility",
            name="side",
            field=models.CharField(
                choices=[
                    ("papermoon", "O que a PaperMoon entrega"),
                    ("client", "O que o cliente faz"),
                ],
                max_length=10,
                verbose_name="Coluna",
            ),
        ),
    ]
