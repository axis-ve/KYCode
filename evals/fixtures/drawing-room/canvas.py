def resize(width, height, scale):
    return round(width * scale), round(height * scale)

def preview(width, height):
    return resize(width, height, 0.5)
