from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import PerformanceFilterForm, SaleForm, UploadFileForm
from .models import Sale
from .services import CSVImportError, import_sales_csv


def _visible_sales(request: HttpRequest):
    queryset = Sale.objects.select_related("product", "seller")
    return queryset if request.user.is_staff else queryset.filter(seller=request.user)


def _summary(queryset):
    values = queryset.aggregate(
        total_sales=Sum("total_price", default=Decimal("0")),
        total_quantity=Sum("quantity", default=0),
        transaction_count=Count("id"),
        product_count=Count("product", distinct=True),
    )
    return values


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        next_url = request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect("home")
    return render(request, "login.html", {"form": form})


@login_required
def home_view(request: HttpRequest) -> HttpResponse:
    sales = _visible_sales(request)
    return render(request, "home.html", {"summary": _summary(sales), "recent_sales": sales[:8]})


@login_required
def upload_view(request: HttpRequest) -> HttpResponse:
    form = UploadFileForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            count = import_sales_csv(form.cleaned_data["file"], request.user)
        except CSVImportError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"{count} vente(s) importée(s) avec succès.")
            return redirect("home")
    return render(request, "upload.html", {"form": form})


@login_required
def add_sales_view(request: HttpRequest) -> HttpResponse:
    form = SaleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        sale = form.save(commit=False)
        sale.seller = request.user
        sale.save()
        messages.success(request, "La vente a été enregistrée.")
        return redirect("home")
    return render(request, "add_sales.html", {"form": form})


@login_required
def performance_view(request: HttpRequest) -> HttpResponse:
    form = PerformanceFilterForm(request.GET or None)
    sales = _visible_sales(request)
    if form.is_valid():
        if form.cleaned_data.get("start_date"):
            sales = sales.filter(date__date__gte=form.cleaned_data["start_date"])
        if form.cleaned_data.get("end_date"):
            sales = sales.filter(date__date__lte=form.cleaned_data["end_date"])

    daily = list(
        sales.annotate(day=TruncDate("date"))
        .values("day")
        .annotate(revenue=Sum("total_price"), transactions=Count("id"))
        .order_by("day")
    )
    chart_data = {
        "labels": [item["day"].isoformat() for item in daily],
        "revenue": [float(item["revenue"]) for item in daily],
        "transactions": [item["transactions"] for item in daily],
    }
    return render(
        request,
        "performance.html",
        {"form": form, "chart_data": chart_data, "summary": _summary(sales)},
    )


@login_required
def summary_view(request: HttpRequest) -> HttpResponse:
    sales = _visible_sales(request)
    by_product = sales.values("product__name").annotate(
        revenue=Sum("total_price"), quantity=Sum("quantity"), transactions=Count("id")
    ).order_by("-revenue")[:20]
    return render(request, "summary.html", {"summary": _summary(sales), "by_product": by_product})


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("login")
