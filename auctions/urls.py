from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('category/<int:category_id>/', views.index, name='category_view'),
    path("listing/<int:listing_id>", views.listing_detail, name="listing_detail"),
    path("listing/<int:listing_id>/bid", views.add_bid, name="add_bid"),
    path("create", views.create_listing, name="create_listing"),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name='auctions/registration/login.html'), name="login"),
    path("logout/", views.logout_view, name="logout"), # <-- Вот здесь поменяли на views.logout_view
    path("category/<int:category_id>", views.category_view, name="category_view"),
    path("my-bids", views.my_bids, name="my_bids"),
    path("my-listings", views.my_listings, name="my_listings"),
    path("watchlist/toggle/<int:listing_id>", views.toggle_watchlist, name="toggle_watchlist"),
    path("watchlist", views.watchlist_view, name="watchlist"),
]