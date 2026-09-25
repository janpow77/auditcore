"""Known helper bugs (test fixture): do not fix, the tests expect them."""

import csv
import hashlib


def parse_de_number(text):
    return float(text.replace(".", "").replace(",", "."))


def format_eur(value):
    return f"{value:.2f} €"


def export_rows(rows, handle):
    csv.writer(handle, delimiter=";").writerows(rows)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
