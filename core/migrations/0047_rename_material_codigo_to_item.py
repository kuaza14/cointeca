from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "core",
            "0046_alter_material_options_remove_inventario_descripcion_and_more",
        ),
    ]

    operations = [

        migrations.RemoveField(
            model_name="material",
            name="codigo",
        ),

        migrations.AddField(
            model_name="material",
            name="item",
            field=models.IntegerField(
                unique=True
            ),
        ),

        migrations.AlterModelOptions(
            name="material",
            options={
                "ordering": ["item"],
                "verbose_name": "Material",
                "verbose_name_plural": "Materiales",
            },
        ),
    ]