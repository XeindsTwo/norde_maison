from django.urls import path
from .views import (
    CartView,
    AddToCartView,
    UpdateCartItemView,
    DeleteCartItemView,
)

urlpatterns = [
    path("", CartView.as_view()),
    path("add/", AddToCartView.as_view()),
    path("item/<int:pk>/", UpdateCartItemView.as_view()),
    path("item/<int:pk>/delete/", DeleteCartItemView.as_view()),
]