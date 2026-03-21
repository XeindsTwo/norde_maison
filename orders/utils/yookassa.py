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
            "return_url": f"{settings.SITE_URL_CLIENT}/checkout?order={order.order_number}"
        },
        "capture": True,
        "description": f"Заказ №{order.order_number}",
        "metadata": {"order_id": order.id}
    }, idempotence_key)

    print(f"✅ create_payment: created payment_id={payment.id} for order {order.order_number}")
    return payment


def check_payment_status(payment_id):
    print(f"🔍 check_payment_status: querying payment_id={payment_id}")
    payment = yookassa.Payment.find_one(payment_id)
    print(f"📋 payment.status = {payment.status}")
    return payment.status == "succeeded"