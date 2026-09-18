from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Product, Sale
from .services import CSVImportError, import_sales_csv

User = get_user_model()


class SaleModelTests(TestCase):
    def test_total_is_calculated_with_decimal_precision(self):
        user = User.objects.create_user("alice", password="safe-password")
        product = Product.objects.create(name="Clavier")
        sale = Sale.objects.create(product=product, price=Decimal("19.95"), quantity=3, seller=user)
        self.assertEqual(sale.total_price, Decimal("59.85"))


class CSVImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="safe-password")

    @staticmethod
    def upload(content: str):
        return SimpleUploadedFile("sales.csv", content.encode("utf-8"), content_type="text/csv")

    def test_import_creates_products_and_sales(self):
        count = import_sales_csv(
            self.upload("Product;Price;Quantity;Date\nClavier;49,90;2;2026-09-18 10:30\n"),
            self.user,
        )
        self.assertEqual(count, 1)
        sale = Sale.objects.get()
        self.assertEqual(sale.product.name, "Clavier")
        self.assertEqual(sale.total_price, Decimal("99.80"))
        self.assertEqual(sale.seller, self.user)

    def test_invalid_file_creates_nothing(self):
        with self.assertRaises(CSVImportError):
            import_sales_csv(
                self.upload("Product;Price;Quantity;Date\nValide;10;1;2026-09-18\nInvalide;abc;2;2026-09-18\n"),
                self.user,
            )
        self.assertFalse(Sale.objects.exists())
        self.assertFalse(Product.objects.exists())

    def test_missing_columns_are_rejected(self):
        with self.assertRaisesMessage(CSVImportError, "Colonnes manquantes"):
            import_sales_csv(self.upload("Product;Price\nClavier;10\n"), self.user)


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="safe-password")
        self.other_user = User.objects.create_user("bob", password="safe-password")
        self.product = Product.objects.create(name="Écran")
        self.own_sale = Sale.objects.create(product=self.product, price=100, quantity=2, seller=self.user)
        self.other_sale = Sale.objects.create(product=self.product, price=900, quantity=1, seller=self.other_user)
        self.client.force_login(self.user)

    def test_home_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")

    def test_user_only_sees_own_sales(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "200,00")
        self.assertNotContains(response, "900,00")

    def test_staff_sees_all_sales(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["summary"]["transaction_count"], 2)

    def test_end_date_includes_the_whole_day(self):
        day = timezone.localdate(self.own_sale.date)
        response = self.client.get(reverse("performance"), {"start_date": day, "end_date": day})
        self.assertEqual(response.context["summary"]["transaction_count"], 1)

    def test_reversed_date_range_is_invalid(self):
        today = timezone.localdate()
        response = self.client.get(
            reverse("performance"),
            {"start_date": today, "end_date": today - timedelta(days=1)},
        )
        self.assertFormError(response.context["form"], None, "La date de début doit précéder la date de fin.")

    def test_logout_only_accepts_post(self):
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))

    def test_manual_sale_creates_a_new_product(self):
        response = self.client.post(
            reverse("add_sales"),
            {"product_name": "Souris", "price": "25.50", "quantity": 2, "date": "2026-09-18T12:00"},
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(Sale.objects.filter(product__name="Souris", seller=self.user, total_price="51.00").exists())
