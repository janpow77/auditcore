def sum_positive(values):
    total = 0
    for value in values:
        if value is not None and value > 0:
            total += value
    return round(total, 2)
