from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True, verbose_name="Название серии")
    image = models.ImageField(upload_to="category_logos/", blank=True, null=True, verbose_name="Логотип серии")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Minifigure(models.Model):
    fig_num = models.CharField(max_length=32, unique=True, db_index=True, verbose_name="Артикул BrickLink")
    name = models.CharField(max_length=255, verbose_name="Название фигурки")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="minifigures", verbose_name="Серия")
    default_image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL изображения")

    class Meta:
        verbose_name = "Минифигурка"
        verbose_name_plural = "Минифигурки"
        ordering = ["fig_num"]

    def __str__(self):
        return f"{self.name} ({self.fig_num})"


class Listing(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название лота")
    description = models.TextField(blank=True, verbose_name="Описание")
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стартовая цена")
    current_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Текущая цена")
    image = models.ImageField(upload_to="listings/", blank=True, null=True, verbose_name="Основное фото")
    image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Внешний URL фото")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="listings", verbose_name="Категория")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings", verbose_name="Продавец")
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="won_listings", verbose_name="Победитель")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    duration_days = models.PositiveIntegerField(default=3, verbose_name="Длительность (дни)")
    ends_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата окончания")

    class Meta:
        verbose_name = "Лот"
        verbose_name_plural = "Лоты"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.current_price:
            self.current_price = self.starting_bid
        if not self.ends_at:
            base_time = self.created_at or timezone.now()
            self.ends_at = base_time + timezone.timedelta(days=self.duration_days)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (ID: {self.id})"


class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids", verbose_name="Лот")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids", verbose_name="Пользователь")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма ставки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время ставки")

    class Meta:
        verbose_name = "Ставка"
        verbose_name_plural = "Ставки"
        ordering = ["-amount"]

    def __str__(self):
        return f"{self.user.username} поставил {self.amount} на {self.listing.title}"


class Comment(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments", verbose_name="Лот")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments", verbose_name="Автор")
    text = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["created_at"]

    def __str__(self):
        return f"Комментарий от {self.user.username} к {self.listing.title}"


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist", verbose_name="Пользователь")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="watched_by", verbose_name="Лот")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        unique_together = ("user", "listing")

    def __str__(self):
        return f"{self.user.username} следит за {self.listing.title}"