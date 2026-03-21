from django.apps import AppConfig
import threading

class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"
    verbose_name = "Управление заказами"

    def ready(self):
        import orders.signals

        if not hasattr(self, "_started"):
            self._started = True
            orders.signals.check_pending_orders_periodically()