# Changelog – auditcore_tyfindings

## 0.1.0 – 2026-10-04 – erste Fassung (noch nicht veröffentlicht)

Portierung der ToF-Zuordnung aus `modAKB_ToF.bas` (akb-makro, Commit 4799ac6c).

- Profil `efre.tof_2021_2027` 2026.10.1: Katalog der Kommissionstabelle
  „Types of findings 2021–2027“ (86 Unterkategorien, englisches Original,
  deutsche Kurzbezeichnung, Kategorie), Kennziffertabelle mit
  Schlüsselwortregeln und Gold-plating-Kennzeichen („!GP“), Formalregeln für
  nichtfinanzielle Mängel; Fingerabdruck SHA-256 über das kanonische JSON.
- `zuordnen`, `formal_zuordnen`, `katalog`, `kategorie`, `load_profile`;
  Ergebnis `Zuordnung` mit Unterkategorie, Kategorie, Zuordnungsweg,
  Gold-plating und Regelkennung. Kennziffern werden exakt als Text verglichen.
- Tabelle `efre.kuerzungsgrund_zs` 2026.10.1 mit
  `kennziffer_aus_kuerzungsgrund`: nur „0“ (kein Kürzungsgrund) ist sicher,
  „810“ und „890“ sind offen und vom Fachbereich zu befüllen.
- `tools/vba_profil.py` erzeugt und prüft Katalog und Regeln aus dem VBA-Modul.
- Paritätstest gegen eine VBA-Ergebnismappe (lokal, per Umgebungsvariable):
  574 Belege und 46 Mängel ohne Abweichung.
