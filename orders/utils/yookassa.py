import yookassa
from django.conf import settings
from uuid import uuid4

yookassa.Configuration.account_id = settings.YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


def create_payment(order):
    idempotence_key = str(uuid4())

    payment = yookassa.Payment.create({
        "amount": {
            "value": f"{order.total_price:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"{settings.SITE_URL_CLIENT}/checkout/?order={order.order_number}"
        },
        "capture": True,
        "description": f"Заказ №{order.order_number}",
        "metadata": {"order_id": order.id},
        "idempotence_key": idempotence_key
    })
    return payment