"""Regeln und Wortlisten der KI-Namenserkennung."""

from __future__ import annotations

import re
from collections.abc import Callable

NerFn = Callable[[list[str]], list[list[tuple[int, int]]]]
# Namensbestandteil: großer Anfangsbuchstabe, auch mit Bindestrich („Meyer-Lüdenscheidt“).
_NAME_PART = r"[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)*"
# Titel vor einem Namen („Prof. Dr.“, „Dipl.-Ing.“). Mit Titel davor erkennt
# die KI „Prof. Dr. Rainer Zufall“ nicht als Person, ohne Titel schon.
_TITLES = re.compile(r"(?:(?:Prof|Dr|Dipl)\.(?:-[A-Za-zäöü]+\.)?\s*)+")
# Listenform „Nachname, Vorname“ am Zeilenanfang, auch mit Titel davor.
_LIST_NAME = re.compile(
    rf"(?:{_TITLES.pattern})?(?P<last>{_NAME_PART}),[ \t]*(?P<first>{_NAME_PART})(?![\w-])"
)
# Wörter, die die KI gelegentlich als Namen meldet, die aber nie im ganzen
# Dokument nachgesucht werden sollen.
# Kontaktangaben in Briefköpfen und Spaltenköpfen; spaCy hält „Telefon X“
# oft für eine Person, auch im Mustersatz.
_CONTACT_WORDS = frozenset(
    ["Telefon", "Telefonnummer", "Telefax", "Fax", "Tel", "Mobil", "Handy", "Durchwahl"]
)
# Häufige Spaltenköpfe in Belegen und Rechnungen: Der Mustersatz bestätigt
# manche Paare davon als Person („Pos Menge“, „Netto Brutto“). Aus einer
# Zelle oder Kopfzeile belegt, werden sie nur mit Anrede davor nachgesucht;
# was die KI direkt meldet, bleibt Fundstelle. Aus einem Satz oder der
# Listenform neben einem anderen Wort belegt, sind es Nachnamen („Petra
# Preis“, „Menge, Wolfgang“) und gelten wie jeder andere Name; nur aus
# Spaltenköpfen („Summe Netto nach Skonto“) gilt der Beleg als Zellbeleg.
_TABLE_WORDS = frozenset(
    [
        "Pos",
        "Position",
        "Menge",
        "Anzahl",
        "Einheit",
        "Preis",
        "Einzelpreis",
        "Gesamtpreis",
        "Gesamt",
        "Summe",
        "Zwischensumme",
        "Betrag",
        "Netto",
        "Brutto",
        "Steuer",
        "Umsatzsteuer",
        "Mehrwertsteuer",
        "USt",
        "MwSt",
        "Rabatt",
        "Skonto",
        "Kostenart",
        "Bemerkung",
        "Datum",
        "Nummer",
        "Rechnung",
        "Beleg",
    ]
)
_NOT_NAMES = frozenset(
    [
        "Herr",
        "Herrn",
        "Frau",
        "Prof",
        "Dipl",
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
        "Sonntag",
        "Januar",
        "Februar",
        "März",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ]
    + list(_CONTACT_WORDS)
)
# Monatskürzel: „Jan“ ist ein Vorname, „15. Jan. 2026“ aber ein Datum.
_MONTH_ABBREVIATIONS = frozenset(
    ["Jan", "Feb", "Mär", "Apr", "Jun", "Jul", "Aug", "Sep", "Sept", "Okt", "Nov", "Dez"]
)
# Nach einem Artikel ist ein nachgesuchtes Wort ein Substantiv
# („der Richter“, „ein Koch“), kein Name.
_ARTICLE_BEFORE = re.compile(
    r"(?:^|[^\w])(?:der|die|das|dem|den|des|ein|eine|einem|einen|einer|eines)\s+$", re.IGNORECASE
)
# … außer als Teil eines Namenszusatzes („von der Heide“, „van den Berg“).
_NAME_PREFIX_BEFORE = re.compile(
    r"(?:^|[^\w])(?:von|vom|van|zu|zur|ter|de)\s+\w+\s+$", re.IGNORECASE
)
# Monatskürzel im Datum: „15. Jan.“, „Jan. 2026“.
_DAY_BEFORE = re.compile(r"\d{1,2}\.\s*$")
_YEAR_AFTER = re.compile(r"\.\s*\d{2,4}(?!\d)")
# Bestandteile eines KI-Treffers, auch Initialen („J.“) und Buchstaben
# außerhalb des deutschen Alphabets („Çelik“).
_SPAN_PART = re.compile(r"[^\W\d_]+")
# Nachsuche mit Grenze: Ein Wort, das über Zellgrenzen hinweg oder nur aus
# einer Zelle oder Kopfzeile belegt ist und das die KI dort nicht im
# Mustersatz bestätigt, wird höchstens max(Untergrenze, Faktor × direkt
# erkannt) Mal ohne Anrede nachgesucht, sonst gar nicht. „Direkt erkannt“
# zählt verschiedene Fundstellentexte, damit ein Spaltenkopf, der auf jeder
# Seite wiederkehrt, die Grenze nicht hebt. Grund: Ein Fehltreffer („Summe
# Netto“ als Person, zwei Spaltenköpfe nebeneinander) würde sonst jedes
# „Summe“ im Dokument schwärzen. Namen aus einem Satz, der Listenform oder
# dem Mustersatz gelten ohne Grenze: spaCy erkennt einen allein stehenden
# Nachnamen fast nie, ein häufig genannter Name wäre sonst überall lesbar.
_PROPAGATION_FLOOR = 10
_PROPAGATION_FACTOR = 4
# Belege über Zellgrenzen („Klaus / Wagner“ in getrennten Spalten) und
# Zellbelege, deren Name der Mustersatz nur zum Teil bestätigt
# („Auftragnehmer Thomas Berger“ → „Thomas Berger“), bekommen mit
# Bestätigung eine höhere Untergrenze, aber keine Freigabe: Der Mustersatz
# bestätigt so auch Spaltenköpfe („Belegart Auftraggeber“), die dann in
# einer Belegliste in jeder Zeile geschwärzt würden.
_PROPAGATION_FLOOR_CONFIRMED = 50
# Zellbelege bestätigt die KI in einem Mustersatz, Kontaktwörter vorher
# entfernt. Erprobt mit de_core_news_sm: 46 von 47 echten Namen bestätigt;
# bestätigt werden aber auch manche Paare aus Spaltenköpfen („Netto
# Brutto“). Belege über Zellgrenzen hinweg werden deshalb nicht bestätigt.
_CONFIRM_FRAME = "Gestern habe ich {} getroffen."
_CONFIRM_START = _CONFIRM_FRAME.index("{}")
# Anrede oder Titel vor dem Wort: Die Fundstelle bleibt auch über der Grenze.
_SALUTATION_BEFORE = re.compile(
    r"(?:^|[^\w])(?:(?:Herrn?|Frau)\s+|(?:Hr|Fr|Dr|Prof|Dipl)\.(?:\s*-?[A-Za-zäöüÄÖÜ]+\.)*(?:\s*\([A-Z]+\))?\s*)$"
)
_WORD_RUN = re.compile(r"[\w-]+")
_NAME_EDGE = " \t,;:()[]/"
# Abschnitte zwischen harten Grenzen bis zu dieser Wortzahl prüft die KI
# zusätzlich für sich (Tabellenzellen, Listeneinträge). Ein Absatz ist ein
# langer Abschnitt; Teile davon ohne Satzzusammenhang ergäben Fehltreffer
# wie „Förderantrag“.
_SHORT_SEGMENT_WORDS = 6


_TITLE_IN_SPAN = re.compile(r"(?<![\w-])(?:(?:Herrn?|Frau)(?![\w-])|(?:Hr|Fr|Dr|Prof|Dipl)\.)")


# Kleinwörter, die auch in Kopfzeilen stehen („Betrag in EUR“, „Preis je
# Stück“, „Name und Anschrift“), und Abkürzungen („inkl. USt“, „lfd. Nr.“).
# Andere Präpositionen („Antrag von …“, „Rechnung an …“) zählen als Satz.
_NO_CONTEXT = frozenset(
    [
        "in",
        "im",
        "je",
        "pro",
        "bis",
        "und",
        "oder",
        "inkl",
        "zzgl",
        "abzgl",
        "exkl",
        "einschl",
        "bzw",
        "ggf",
        "ggfs",
        "gem",
        "lt",
        "ca",
        "evtl",
        "vgl",
        "usw",
        "lfd",
        "nr",
        "max",
        "min",
    ]
)
