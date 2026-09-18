from decimal import Decimal

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def merge_duplicate_products(apps, schema_editor):
    Product = apps.get_model("dashboard_data_app", "Product")
    Sale = apps.get_model("dashboard_data_app", "Sale")
    canonical_by_name = {}
    for product in Product.objects.order_by("id"):
        canonical = canonical_by_name.setdefault(product.name, product)
        if canonical.pk != product.pk:
            Sale.objects.filter(product_id=product.pk).update(product_id=canonical.pk)
            product.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard_data_app", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(name="product", options={"ordering": ["name"]}),
        migrations.AlterModelOptions(name="sale", options={"ordering": ["-date", "-id"]}),
        migrations.RunPython(merge_duplicate_products, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="product",
            name="name",
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name="sale",
            name="date",
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="sale",
            name="price",
            field=models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))]),
        ),
        migrations.AlterField(
            model_name="sale",
            name="quantity",
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name="sale",
            name="total_price",
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=14),
        ),
        migrations.AlterField(
            model_name="sale",
            name="product",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sales", to="dashboard_data_app.product"),
        ),
        migrations.AlterField(
            model_name="sale",
            name="seller",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sales", to=settings.AUTH_USER_MODEL),
        ),
    ]
