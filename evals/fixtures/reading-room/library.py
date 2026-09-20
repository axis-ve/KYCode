BOOKS = {"atlas": {"title": "Field Atlas", "copies": 3}}

def describe(code):
    book = BOOKS[code]
    return f"{book['title']}: {book['copies']} copies"

def borrow(code, count):
    if count > BOOKS[code]["copies"]:
        return False
    BOOKS[code]["copies"] -= count
    return True
