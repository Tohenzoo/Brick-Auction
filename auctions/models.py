from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=64)
    icon = models.ImageField(upload_to="categories/", blank=True, null=True)

    def __str__(self):
        return self.name

class Minifigure(models.Model):
    fig_num = models.CharField(max_length=32, unique=True, verbose_name="Артикул (LEGO ID)")
    name = models.CharField(max_length=255, verbose_name="Название фигурки")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="minifigures", verbose_name="Серия")
    default_image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Ссылка на фото")

    def __str__(self):
        return f"{self.name} ({self.fig_num})"

class Listing(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    current_bid = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="listings/", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="listings")
    minifigure = models.ForeignKey(Minifigure, on_delete=models.SET_NULL, null=True, blank=True, related_name="listings")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    watchlist = models.ManyToManyField(User, blank=True, related_name="watchlist")
    is_active = models.BooleanField(default=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_finished(self):
        if not self.is_active:
            return True
        if self.end_date and self.end_date <= timezone.now():
            return True
        return False

    def __str__(self):
        return self.title

class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} ₽"
