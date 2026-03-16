from django.urls import path
from .views import CheckoutView, OrderHistoryView, OrderPreviewView

urlpatterns = [
    path("checkout/", CheckoutView.as_view()),
    path("history/", OrderHistoryView.as_view()),
    path("preview/", OrderPreviewView.as_view()),
    ]