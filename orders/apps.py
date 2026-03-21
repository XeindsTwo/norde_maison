from django.apps import AppConfig
import threading

class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"
    verbose_name = "Управление заказами"

    def ready(self):
        import orders.signals
        thread = threading.Thread(
            target=orders.signals.check_pending_orders_periodically,
            daemon=True
        )
        thread.start()