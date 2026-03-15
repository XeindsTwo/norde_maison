import uuid

def generate_order_number():
    return uuid.uuid4().hex[:12].upper()