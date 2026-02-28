from django.urls import path
from .views import (
    FavoriteToggleView,
    FavoriteDeleteView,
    FavoriteListView
)

urlpatterns = [
    path("", FavoriteListView.as_view()),
    path("toggle/", FavoriteToggleView.as_view()),
    path("delete/<int:product_id>/", FavoriteDeleteView.as_view()),
]