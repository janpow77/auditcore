def positive_total(items):
    result = 0
    for item in items:
        if item is not None and item > 0:
            result += item
    return round(result, 2)
