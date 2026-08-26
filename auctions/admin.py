from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Minifigure, Listing, Bid, Comment, Watchlist

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "image")
    search_fields = ("name",)

@admin.register(Minifigure)
class MinifigureAdmin(admin.ModelAdmin):
    list_display = ("fig_num", "name", "category")
    search_fields = ("fig_num", "name")
    list_filter = ("category",)

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "current_price", "category", "owner", "is_active", "ends_at")
    list_filter = ("is_active", "category", "created_at")
    search_fields = ("title", "description")

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "user", "amount", "created_at")
    list_filter = ("created_at",)
    search_fields = ("listing__title", "user__username")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "user", "created_at")
    search_fields = ("listing__title", "user__username", "text")

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "listing", "created_at")