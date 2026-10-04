# Bewusste Verhaltensabweichungen gegenüber `modAKB_ToF.bas`

Die Zuordnungsergebnisse sind gleich (Paritätstest: 574 Belege, 46 Mängel,
0 Abweichungen). Abweichungen betreffen nur die Schnittstelle:

| VBA | auditcore_tyfindings | Grund |
|---|---|---|
| `ToFLaden` liest änderbare Tabellen `tblToFZuordnung` und `tblToFZuordnungFormal` aus dem Blatt „ToF-Katalog“ der Trägermappe und fällt sonst auf den Vorschlag im Modul zurück. | Nur verpackte, versionierte Profile; Änderungen ergeben eine neue Profilversion mit eigenem Fingerabdruck. Eigene Profile lassen sich mit `profil_aus_dict` prüfen und an `zuordnen(…, profil=…)` übergeben. | Nachvollziehbarkeit: jedes Ergebnis ist einer Profilversion zuzuordnen. |
| Nicht zugeordnete Fälle tragen den Text „nicht zugeordnet“ als Unterkategorie und eine leere Kategorie. | `tof_unterkategorie` und `tof_kategorie` sind `None`; `Zuordnung.anzeige` liefert den VBA-Text. | Kein Sonderwert in einem Nummernfeld. |
| `ToFText` wandelt als Zahl gespeicherte Unterkategorien in Text um; Kennziffern kommen über `ToKey` als Text. | Kennziffer und Beschreibung müssen Text sein, sonst `EingabeFehler`. `kennziffer_normalisieren` übernimmt `ToKey` (Ränder, geschütztes Leerzeichen, „-“/„/“) und die Regel „leer → ohne Kennziffer“ aus `modAKB_Import`. | „1.1“ ≠ „1.10“ lässt sich nur als Text sicher unterscheiden. |
| Der Zuordnungsweg einer Zeile ohne Unterkategorie (z. B. 8.3) ist „nicht zugeordnet“ ohne Regelangabe. | Gleicher Weg; `regel_id` nennt zusätzlich die Tabellenzeile (`kennziffer:8.3`). | Herkunft der Entscheidung sichtbar. |
| Die Tabelle der Kürzungsgründe gibt es in VBA nicht. | `efre.kuerzungsgrund_zs`, bewusst unvollständig. | Vorbereitung für FlowInvoice; Werte vom Fachbereich. |
