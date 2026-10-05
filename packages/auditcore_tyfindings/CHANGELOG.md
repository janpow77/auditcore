# Changelog – auditcore_tyfindings

## 0.2.0 – 2026-10-05 – deutsche Kategoriebezeichnungen als Standard

- `STANDARDPROFIL` ist jetzt `efre.tof_2021_2027` 2026.10.2 (Fingerabdruck
  `f83a36f21f57605f85a117cd7b004ae9ce04c42fcb73b749c34e189970ad7ebf`);
  `zuordnen`, `formal_zuordnen` und `katalog` liefern ohne `profil` die
  Einträge mit `kategorie_de`. Regeln, Katalog und Zuordnungsergebnisse sind
  unverändert. 2026.10.1 bleibt über `load_profile` ladbar.
- Profil `efre.tof_2021_2027` 2026.10.2 (abgeleitet aus 2026.10.1): Feld `kategorie_de` je Katalogeintrag mit den deutschen
  Kategoriebezeichnungen, fachlich freigegeben am 05.10.2026; maßgeblich ist die
  Fassung der AKB-Auswertung (`ToFKategorieDe` in `modAKB_ToF.bas`, Entscheidung
  05.10.2026), identisch mit der FlowInvoice-Übergangstabelle. Neu `ToFEintrag.kategorie_de` (Standard `None`)
  und `ToFProfil.kategorie_de(kategorie)`; der Profillader prüft, dass
  `kategorie_de` vollständig und je Kategorie einheitlich ist, und akzeptiert
  `derived_from`.

## 0.1.0 – 2026-10-04 – erste Fassung (veröffentlicht mit v0.8.0)

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
