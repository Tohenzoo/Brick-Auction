from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.utils import timezone  # <--- Обязательно должно быть здесь
from datetime import timedelta     # <--- И это тоже
from .models import Listing, Category, Bid, ListingImage
from .forms import ListingForm, CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Bid
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

@login_required
def my_bids(request):
    # Находим все ставки текущего пользователя
    user_bids = Bid.objects.filter(user=request.user).select_related('listing', 'listing/category')
    
    # Чтобы не выводить один и тот же лот несколько раз, если пользователь делал много ставок на один товар, 
    # можно оставить уникальные лоты или отсортировать их:
    # Собираем уникальные лоты, на которые пользователь делал ставки
    listing_ids = user_bids.values_list('listing', flat=True).distinct()
    listings = Listing.objects.filter(id__in=listing_ids)

    return render(request, "auctions/my_bids.html", {
        "listings": listings
    })

def index(request, category_id=None):
    categories = Category.objects.all()
    
    # Базовая фильтрация
    if category_id:
        listings = Listing.objects.filter(is_active=True, category_id=category_id)
    else:
        listings = Listing.objects.filter(is_active=True)
    
    # Логика сортировки
    sort_by = request.GET.get('sort')
    if sort_by == 'price_low':
        listings = listings.order_by('current_bid')
    elif sort_by == 'price_high':
        listings = listings.order_by('-current_bid')
    elif sort_by == 'newest':
        listings = listings.order_by('-created_at')
    
    return render(request, "auctions/index.html", {
        "listings": listings,
        "categories": categories,
        "selected_category": category_id,
        "current_sort": sort_by
    })

def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    return render(request, "auctions/listing.html", {
        "listing": listing
    })

def add_bid(request, listing_id):
    if request.method == "POST":
        listing = get_object_or_404(Listing, pk=listing_id)
        try:
            bid_increment = float(request.POST.get("bid_amount"))
        except (TypeError, ValueError):
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "error_message": "Введите корректную сумму."
            })

        current_price = listing.current_bid if listing.current_bid else listing.starting_bid
        new_amount = float(current_price) + bid_increment

        new_bid = Bid(
            listing=listing,
            user=request.user if request.user.is_authenticated else None,
            amount=new_amount
        )
        new_bid.save()
        listing.current_bid = new_amount
        listing.save()

        return HttpResponseRedirect(reverse("listing_detail", args=[listing.id]))
            
    return HttpResponseRedirect(reverse("listing_detail", args=[listing_id]))

@login_required
def toggle_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if request.user in listing.watchlist.all():
        listing.watchlist.remove(request.user)
        added = False
    else:
        listing.watchlist.add(request.user)
        added = True
    
    # Если это AJAX-запрос, возвращаем JSON вместо перезагрузки
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'added': added})
        
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('index')))

@login_required
def watchlist_view(request):
    listings = request.user.watchlist_listings.all()
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

# --- НОВАЯ ФУНКЦИЯ ДЛЯ СОЗДАНИЯ ЛОТА ---
@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            new_listing = form.save(commit=False)
            new_listing.owner = request.user
            
            images = request.FILES.getlist('image')
            
            if images:
                new_listing.image = images[0] # Первая картинка — обложка
            
            new_listing.save()
            
            if len(images) > 1:
                for img in images[1:]:
                    ListingImage.objects.create(listing=new_listing, image=img)
                    
            return redirect('index')
    else:
        form = ListingForm()
    
    return render(request, "auctions/create_listing.html", {
        "form": form
    })

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Автоматически логиним пользователя
            return redirect('index') # Перенаправляем на главную
    else:
        form = CustomUserCreationForm()
    
    return render(request, "auctions/registration/register.html", {
        "form": form
    })

from django.contrib.auth import logout # Убедитесь, что logout импортирован

def logout_view(request):
    logout(request)
    return redirect('index')

def category_view(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    # Выбираем только активные лоты выбранной категории
    listings = Listing.objects.filter(is_active=True, category=category).order_by('-created_at')
    categories = Category.objects.all()
    
    return render(request, "auctions/index.html", {
        "listings": listings,
        "categories": categories,
        "selected_category": category # Чтобы знать, какая категория сейчас выбрана (по желанию)
    })

def add_bid(request, listing_id):
    if request.method == "POST":
        listing = get_object_or_404(Listing, pk=listing_id)
        bid_increment = float(request.POST.get("bid_amount"))

        # Валидация шага ставки
        if not (100 <= bid_increment <= 300):
            return render(request, "auctions/listing.html", {"listing": listing, "error_message": "Шаг ставки 100-300 руб."})

        # Логика продления (если ставка в последний час)
        if timezone.now() + timedelta(hours=1) >= listing.end_date:
            listing.end_date = timezone.now() + timedelta(hours=1)
            listing.save()

        # Создаем ставку
        new_amount = float(listing.current_bid or listing.starting_bid) + bid_increment
        Bid.objects.create(listing=listing, user=request.user, amount=new_amount)
        listing.current_bid = new_amount
        listing.save()
        
        return HttpResponseRedirect(reverse("listing_detail", args=[listing.id]))

@login_required
def my_listings(request):
    # Получаем все лоты, владельцем которых является текущий пользователь
    listings = Listing.objects.filter(owner=request.user).order_by('-created_at')
    
    return render(request, "auctions/my_listings.html", {
        "listings": listings
    })

@login_required
def my_bids(request):
    # Получаем все лоты, на которые пользователь делал ставки
    user_bids = Bid.objects.filter(user=request.user).select_related('listing')
    listing_ids = user_bids.values_list('listing', flat=True).distinct()
    
    all_bids_listings = Listing.objects.filter(id__in=listing_ids)
    
    active_listings = []
    past_listings = [] # Проигранные или завершенные более 1 дня назад
    
    now = timezone.now()
    
    for listing in all_bids_listings:
        # Проверяем, истек ли 1 день с момента окончания торгов (если задано поле end_date)
        # Если у вас нет поля end_date, ориентируемся на listing.is_active
        is_expired = False
        if hasattr(listing, 'end_date') and listing.end_date:
            if now > listing.end_date + timedelta(days=1):
                is_expired = True
        
        if listing.is_active and not is_expired:
            active_listings.append(listing)
        else:
            past_listings.append(listing)

    return render(request, "auctions/my_bids.html", {
        "active_listings": active_listings,
        "past_listings": past_listings
    })