"""Ressourcengrenzen beim Einlesen (im Original nicht vorhanden, DC-C03).

Die Vorgaben sind so bemessen, dass alle charakterisierten Originalfälle
unverändert durchlaufen; Anwendungen können sie ausdrücklich verschärfen.
Der ecohesion-Worker des Originals begrenzte CPU-Zeit und Adressraum per
``resource.setrlimit`` im eigenen Prozess – das bleibt Sache der Anwendung.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadLimits:
    #: Größe der Eingabedatei auf dem Datenträger.
    max_file_bytes: int = 512 * 1024 * 1024
    #: Entpackte Größe von ``word/document.xml`` (Schutz vor ZIP-Bomben).
    max_xml_bytes: int = 128 * 1024 * 1024
    #: Seitenzahl eines PDF nach der Textextraktion.
    max_pdf_pages: int = 5000
    #: Zeitlimit für ``pdftotext`` in Sekunden (Original: 120).
    pdftotext_timeout: float = 120.0

    def __post_init__(self) -> None:
        for name in ("max_file_bytes", "max_xml_bytes", "max_pdf_pages"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} muss eine positive ganze Zahl sein")
        if not self.pdftotext_timeout > 0:
            raise ValueError("pdftotext_timeout muss positiv sein")


DEFAULT_LIMITS = ReadLimits()
