from django.contrib import admin
from .models import Category, Listing, Bid, Minifigure

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

@admin.register(Minifigure)
class MinifigureAdmin(admin.ModelAdmin):
    list_display = ("fig_num", "name", "category")
    search_fields = ("fig_num", "name")
    list_filter = ("category",)

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "current_bid", "is_active", "end_date")
    search_fields = ("title",)

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("user", "listing", "amount", "timestamp")