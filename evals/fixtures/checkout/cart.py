CATALOG = {'tea': 1200}

def display_price(sku):
    return f'${CATALOG[sku] / 100:.2f}'

def checkout_payload(sku, quantity):
    return {'amount_cents': CATALOG[sku] * quantity * 100, 'currency': 'usd'}
