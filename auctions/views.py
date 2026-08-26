import json
import urllib.request
import urllib.error
import re
from datetime import timedelta
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q

from .models import Listing, Bid, Category, Minifigure, Watchlist


def lookup_minifig(request):
    """Поиск фигурки с получением реального имени на английском языке."""
    raw_query = request.GET.get("code", "").strip().lower()
    if not raw_query:
        return JsonResponse({"found": False})

    variants = [raw_query]
    m = re.match(r'^([a-z]+)0*(\d+)([a-z]*)$', raw_query)
    if m:
        prefix, num_str, suffix = m.groups()
        num_int = int(num_str)
        variants.extend([
            f"{prefix}{num_int:04d}{suffix}",
            f"{prefix}{num_int:03d}{suffix}",
            f"{prefix}{num_int}{suffix}"
        ])
    variants = list(dict.fromkeys(variants))

    # 1. Проверяем локальную базу
    minifig = Minifigure.objects.filter(fig_num__in=variants).select_related("category").first()
    if minifig and "character (" not in minifig.name.lower() and not minifig.name.lower().startswith("minifigure "):
        cat_name = minifig.category.name if minifig.category else ""
        return JsonResponse({
            "found": True,
            "title": f"LEGO {cat_name} {minifig.name} ({raw_query})".replace("  ", " ").strip(),
            "category_id": minifig.category.id if minifig.category else None,
            "image_url": minifig.default_image_url or f"https://img.bricklink.com/ItemImage/MN/0/{raw_query}.png",
        })

    # 2. Определение категории
    cat_map = {
        'sw': 'Star Wars',
        'sh': 'Super Heroes',
        'njo': 'Ninjago',
        'hp': 'Harry Potter',
        'lor': 'LoTR',
        'hob': 'LoTR',
        'col': 'CMF',
        'fig': 'CMF',
        'cas': 'Castle',
        'cty': 'City',
        'poc': 'Pirates of the Caribbean',
    }

    prefix_str = m.group(1) if m else ""
    cat_name = cat_map.get(prefix_str, "")
    cat_obj = Category.objects.filter(name__icontains=cat_name).first() if cat_name else None

    # 3. Запрос точного имени с Brickset
    real_name = ""
    img_url = f"https://img.bricklink.com/ItemImage/MN/0/{raw_query}.png"

    for code_var in variants:
        try:
            url = f"https://brickset.com/minifigs/{code_var}"
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                html = resp.read().decode('utf-8', errors='ignore')

                title_match = re.search(r'<title>[^:]+:\s*([^|<]+)\s*\|', html, re.IGNORECASE)
                if title_match:
                    name_candidate = title_match.group(1).strip()
                    if name_candidate and "not found" not in name_candidate.lower():
                        real_name = name_candidate
                        break

                og_match = re.search(r'property="og:title"\s+content="[^:]+:\s*([^"]+)"', html, re.IGNORECASE)
                if og_match:
                    real_name = og_match.group(1).strip()
                    break
        except Exception:
            continue

    if not real_name:
        return JsonResponse({"found": False})

    for code_var in variants:
        Minifigure.objects.update_or_create(
            fig_num=code_var,
            defaults={
                'name': real_name,
                'category': cat_obj,
                'default_image_url': img_url
            }
        )

    full_title = f"LEGO {cat_name} {real_name} ({raw_query})".replace("  ", " ").strip()

    return JsonResponse({
        "found": True,
        "title": full_title,
        "category_id": cat_obj.id if cat_obj else None,
        "image_url": img_url,
    })


def index(request):
    """Главная страница со списком активных лотов и кастомной сортировкой серий."""
    category_id = request.GET.get("category")
    sort = request.GET.get("sort")
    search_query = request.GET.get("q", "").strip()
    now = timezone.now()

    listings = Listing.objects.filter(is_active=True).filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=now)
    )

    # 1. Задаем нужный порядок и названия
    all_categories = list(Category.objects.all())
    target_names = ['Star Wars', 'Ninjago', 'Super Heroes', 'LoTR', 'Harry Potter', 'CMF']
    
    display_categories = []
    main_cat_ids = []

    for name in target_names:
        # Ищем категорию (учитываем, что LoTR в БД может называться Lord of the Rings)
        cat = next((c for c in all_categories if c.name.lower() == name.lower() or (name == 'LoTR' and c.name.lower() == 'lord of the rings')), None)
        if cat:
            cat.display_name = name  # Принудительно ставим короткое имя для шаблона
            display_categories.append(cat)
            main_cat_ids.append(cat.id)

    # 2. Обработка фильтрации (включая "Разное")
    if category_id == "other":
        listings = listings.exclude(category_id__in=main_cat_ids)
        selected_category = "other"
    elif category_id:
        try:
            listings = listings.filter(category_id=int(category_id))
            selected_category = int(category_id)
        except ValueError:
            selected_category = None
    else:
        selected_category = None

    # 3. Поиск и сортировка
    if search_query:
        listings = listings.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    if sort == "newest":
        listings = listings.order_by("-id")
    elif sort == "price_low":
        listings = listings.order_by("current_price")
    elif sort == "price_high":
        listings = listings.order_by("-current_price")
    else:
        listings = listings.order_by("-created_at")

    return render(request, "auctions/index.html", {
        "listings": listings,
        "display_categories": display_categories,
        "selected_category": selected_category,
        "current_sort": sort,
        "search_query": search_query,
    })

def category_view(request, category_id):
    """Просмотр лотов конкретной категории."""
    category = get_object_or_404(Category, id=category_id)
    now = timezone.now()

    listings = Listing.objects.filter(category=category, is_active=True).filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=now)
    ).order_by("-created_at")

    categories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings": listings,
        "categories": categories,
        "selected_category": category.id,
    })


def listing_detail(request, listing_id):
    """Детальная страница лота."""
    listing = get_object_or_404(Listing, id=listing_id)
    bids = Bid.objects.filter(listing=listing).order_by("-amount")

    is_in_watchlist = False
    if request.user.is_authenticated:
        is_in_watchlist = Watchlist.objects.filter(user=request.user, listing=listing).exists()

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bids": bids,
        "is_in_watchlist": is_in_watchlist,
    })


@login_required
def add_bid(request, listing_id):
    """Прием ставки."""
    listing = get_object_or_404(Listing, id=listing_id)
    now = timezone.now()

    if not listing.is_active or (listing.ends_at and listing.ends_at <= now) or request.user == listing.owner:
        return redirect("listing_detail", listing_id=listing.id)

    if request.method == "POST":
        try:
            bid_amount = Decimal(request.POST.get("bid_amount", "0"))
        except (ValueError, TypeError):
            bid_amount = Decimal("0")

        current_highest = listing.current_price if listing.current_price > 0 else listing.starting_bid

        if bid_amount > current_highest:
            Bid.objects.create(user=request.user, listing=listing, amount=bid_amount)
            listing.current_price = bid_amount
            listing.save()

    return redirect("listing_detail", listing_id=listing.id)


@login_required
def toggle_watchlist(request, listing_id):
    """Добавление/удаление лота из избранного."""
    listing = get_object_or_404(Listing, id=listing_id)
    watchlist_item = Watchlist.objects.filter(user=request.user, listing=listing).first()
    
    if watchlist_item:
        watchlist_item.delete()
    else:
        Watchlist.objects.create(user=request.user, listing=listing)
        
    return redirect("listing_detail", listing_id=listing.id)


@login_required
def watchlist_view(request):
    """Список избранных лотов пользователя."""
    watched_items = Watchlist.objects.filter(user=request.user).select_related("listing")
    listings = [item.listing for item in watched_items]
    return render(request, "auctions/watchlist.html", {"listings": listings})


@login_required
def my_bids(request):
    """Раздельный вывод активных и завершенных лотов, где участвовал пользователь."""
    user_bids = Bid.objects.filter(user=request.user).select_related("listing")
    listing_ids = user_bids.values_list("listing_id", flat=True).distinct()
    all_bids_listings = Listing.objects.filter(id__in=listing_ids).order_by("-created_at")

    now = timezone.now()
    active_listings = []
    past_listings = []

    for listing in all_bids_listings:
        if not listing.is_active or (listing.ends_at and listing.ends_at <= now):
            past_listings.append(listing)
        else:
            active_listings.append(listing)

    return render(request, "auctions/my_bids.html", {
        "active_listings": active_listings,
        "past_listings": past_listings,
    })


@login_required
def my_listings(request):
    """Список лотов, созданных текущим пользователем."""
    listings = Listing.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "auctions/my_listings.html", {"listings": listings})


@login_required
def create_listing(request):
    """Создание лота."""
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        
        try:
            starting_bid = Decimal(request.POST.get("starting_bid", "0"))
        except (ValueError, TypeError):
            starting_bid = Decimal("0")

        category_id = request.POST.get("category")
        duration_days = int(request.POST.get("duration_days", 3))
        category = get_object_or_404(Category, id=category_id) if category_id else None

        listing = Listing(
            title=title,
            description=description,
            starting_bid=starting_bid,
            current_price=starting_bid,
            category=category,
            owner=request.user,
            duration_days=duration_days,
            is_active=True,
        )

        uploaded_files = request.FILES.getlist("images")
        if uploaded_files:
            listing.image = uploaded_files[0]

        listing.save()
        return redirect("index")

    categories = Category.objects.all()
    return render(request, "auctions/create_listing.html", {"categories": categories})


def register(request):
    """Регистрация нового пользователя."""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirmation = request.POST.get("confirmation", "")

        if password != confirmation:
            return render(request, "auctions/register.html", {"message": "Пароли не совпадают."})

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
        except Exception:
            return render(request, "auctions/register.html", {"message": "Пользователь с таким именем уже существует."})

        login(request, user)
        return redirect("index")

    return render(request, "auctions/register.html")