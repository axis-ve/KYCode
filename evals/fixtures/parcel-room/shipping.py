RATES = {"small": 450, "large": 900}

def label(size):
    return f"${RATES[size] / 100:.2f}"

def quote(size, count):
    return {"amount_cents": RATES[size] * count * 100, "currency": "usd"}
