from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("category/<int:category_id>/", views.category_view, name="category_view"),
    path("listing/<int:listing_id>/", views.listing_detail, name="listing_detail"),
    path("listing/<int:listing_id>/bid", views.add_bid, name="add_bid"),
    path("listing/<int:listing_id>/watchlist", views.toggle_watchlist, name="toggle_watchlist"),
    
    # Маршрут для автопоиска артикула:
    path("lookup-minifig/", views.lookup_minifig, name="lookup_minifig"),
    
    path("watchlist/", views.watchlist_view, name="watchlist"),
    path("my-bids/", views.my_bids, name="my_bids"),
    path("my-listings/", views.my_listings, name="my_listings"),
    path("create/", views.create_listing, name="create_listing"),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="auctions/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="index"), name="logout"),
]