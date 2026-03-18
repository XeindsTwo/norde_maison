from decimal import Decimal

EXCHANGE_RATES = {
    'rub': {'rub': Decimal('1.0'), 'kzt': Decimal('5.5'), 'byn': Decimal('0.0366')},
    'kzt': {'rub': Decimal('0.182'), 'kzt': Decimal('1.0'), 'byn': Decimal('0.00605')},
    'byn': {'rub': Decimal('27.35'), 'kzt': Decimal('165.45'), 'byn': Decimal('1.0')},
}

def convert_to_rub(price, from_currency):
    """
    Конвертирует любую цену из валюты в рубли.
    price: Decimal
    from_currency: str ('rub', 'kzt', 'byn')
    """
    rate = EXCHANGE_RATES[from_currency]['rub']
    return price * rate

def get_delivery_price_in_rub(delivery_price, currency):
    """
    Получает цену доставки в рублях из локальной валюты.
    delivery_price: Decimal
    currency: str
    """
    return convert_to_rub(delivery_price, currency)