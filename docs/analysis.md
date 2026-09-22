# Ausgangsanalyse und Auslegungsentscheidungen

Ausgangscommit: b2f898cc0777a5d81833c8f549f61c7ab64a443e.
Der Arbeitsordner war leer; das bestehende GitHub-Repository wurde geklont.
Vorhanden: MIT-Lizenz und docs/auditcore_lastenheft.md, Version 1.5.
Keine Packages, Implementierungen, Tests, CI oder Projektkonfiguration vorhanden.
Die vollständige Spezifikation (5667 Zeilen) wurde vor Implementierung gelesen.

Abweichungen und Auflösung:
- AUDITCORE_LASTENHEFT.md ist ein Verweis auf die vorhandene Datei; keine zweite Wahrheit.
- Punktierte Dateipfade in älteren Beispielen werden auf src/auditcore/tools/* abgebildet.
- Die explizite Ein-Projekt-Vorgabe geht älteren Aussagen über separate Bibliotheken vor.
- auditcore-bibquality bleibt als Alias von auditcore-quality erhalten.
- Fachdomains entstehen erst aus belegten Kandidaten; keine erfundenen Rechtsregeln.
- Frameworkquelle: janpow77/verwaltung-app-framework, Commit
  15f5338f783f2c7d5760a9bb299be06d27326be0; frischer separater Checkout,
  vorhandene lokale Änderungen am Framework werden nicht berührt.
- F-01 bis F-18 erfordern jeweils Klärung (MUSS); technische Konkretisierungen
  werden getrennt als BEDINGT bewertet. Empfehlungen bleiben SOLL.
- Neue oder geänderte Quellanforderungen benötigen eine überprüfte Adapterzuordnung;
  unbekannte Semantik wird REVIEW_REQUIRED statt ungeprüfter Durchsetzung.
- Inventare und externe Quellcheckouts verbleiben unter .auditcore (nicht in Git).
- Die Fachbibliothek importiert niemals Tools. Policy- und Infrastrukturcode liegt in Tools.
