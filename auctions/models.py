from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Listing(models.Model):
    title = models.CharField(max_length=200)
    article = models.CharField(max_length=20, blank=True, null=True) # Новое поле для артикула
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    current_bid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to='listings/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="listings")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    watchlist = models.ManyToManyField(User, blank=True, related_name="watchlist_listings")

    # Состояние фигурки
    CONDITION_CHOICES = [
        ('new', 'Новое'),
        ('used', 'Б/у'),
    ]
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='new')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Если создается новый лот, рассчитываем end_date (3 дня + 20:00 МСК)
        if not self.pk:
            three_days_later = timezone.now() + timedelta(days=3)
            self.end_date = three_days_later.replace(hour=20, minute=0, second=0, microsecond=0)
        super().save(*args, **kwargs)

class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bid {self.amount} by {self.user.username} on {self.listing.title}"

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='listings/extra/')

    def __str__(self):
        return f"Photo for {self.listing.title}"

