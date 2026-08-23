from django.contrib import admin
from .models import Category, Listing, Bid, ListingImage

# Создаем инлайн-класс для дополнительных фото
class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 3  # Количество пустых строк для загрузки по умолчанию
    max_num = 10  # Максимальное количество фото

# Регистрируем модель Listing с использованием этого инлайна
class ListingAdmin(admin.ModelAdmin):
    inlines = [ListingImageInline]

admin.site.register(Category)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Bid)