import csv
import io
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from .models import Product, Sale

REQUIRED_COLUMNS = {"Product", "Price", "Quantity", "Date"}
MAX_ROWS = 10_000


class CSVImportError(ValueError):
    pass


@dataclass(frozen=True)
class SaleRow:
    product_name: str
    price: Decimal
    quantity: int
    date: datetime


def _parse_datetime(value: str) -> datetime:
    parsed = parse_datetime(value.strip())
    if parsed is None:
        parsed_date = parse_date(value.strip())
        if parsed_date:
            parsed = datetime.combine(parsed_date, time.min)
    if parsed is None:
        raise ValueError("date invalide")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _parse_row(row: dict[str, str], line_number: int) -> SaleRow:
    try:
        product_name = (row.get("Product") or "").strip()
        if not product_name:
            raise ValueError("produit manquant")
        if len(product_name) > 200:
            raise ValueError("nom de produit trop long")
        price = Decimal((row.get("Price") or "").strip().replace(",", "."))
        quantity = int((row.get("Quantity") or "").strip())
        if price <= 0 or quantity <= 0:
            raise ValueError("prix et quantité doivent être positifs")
        if price > Decimal("9999999999.99") or quantity > 2_147_483_647:
            raise ValueError("prix ou quantité trop élevé")
        if price * quantity > Decimal("999999999999.99"):
            raise ValueError("montant total trop élevé")
        return SaleRow(product_name, price.quantize(Decimal("0.01")), quantity, _parse_datetime(row.get("Date") or ""))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise CSVImportError(f"Ligne {line_number} : {exc}.") from exc


def import_sales_csv(uploaded_file, seller) -> int:
    try:
        text = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CSVImportError("Le fichier doit être encodé en UTF-8.") from exc
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    if not reader.fieldnames:
        raise CSVImportError("Le fichier est vide.")
    missing = REQUIRED_COLUMNS.difference(name.strip() for name in reader.fieldnames)
    if missing:
        raise CSVImportError(f"Colonnes manquantes : {', '.join(sorted(missing))}.")
    parsed_rows = []
    for line_number, row in enumerate(reader, start=2):
        if len(parsed_rows) >= MAX_ROWS:
            raise CSVImportError(f"Le fichier dépasse la limite de {MAX_ROWS:,} lignes.")
        parsed_rows.append(_parse_row(row, line_number))
    if not parsed_rows:
        raise CSVImportError("Le fichier ne contient aucune vente.")
    with transaction.atomic():
        products = {}
        for name in {row.product_name for row in parsed_rows}:
            products[name], _ = Product.objects.get_or_create(name=name)
        Sale.objects.bulk_create(
            [Sale(product=products[row.product_name], price=row.price, quantity=row.quantity, total_price=row.price * row.quantity, seller=seller, date=row.date) for row in parsed_rows],
            batch_size=500,
        )
    return len(parsed_rows)
