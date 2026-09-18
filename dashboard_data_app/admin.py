from django.contrib import admin

from .models import Product, Sale


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "date")
    search_fields = ("name",)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("product", "seller", "quantity", "price", "total_price", "date")
    list_filter = ("seller", "date")
    search_fields = ("product__name", "seller__username")
    autocomplete_fields = ("product", "seller")
    readonly_fields = ("total_price",)
