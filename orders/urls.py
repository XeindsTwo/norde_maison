from django.urls import path
from .views import (
    CheckoutPaymentView,
    YookassaWebhookView,
    CheckoutView,
    OrderHistoryView,
    OrderPreviewView,
    OrderStatusView,
    PaymentStatusView,
    CurrentPendingOrderView
)

urlpatterns = [
    path("checkout/payment/", CheckoutPaymentView.as_view(), name="checkout-payment"),
    path("yookassa/webhook/", YookassaWebhookView.as_view(), name="yookassa-webhook"),
    path("<str:order_number>/status/", OrderStatusView.as_view(), name="order-status"),
    path("payment/<str:payment_id>/status/", PaymentStatusView.as_view(), name="payment-status"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("checkout/current-pending/", CurrentPendingOrderView.as_view(), name="current-pending-order"),
    path("history/", OrderHistoryView.as_view(), name="order-history"),
    path("preview/", OrderPreviewView.as_view(), name="order-preview"),
]
