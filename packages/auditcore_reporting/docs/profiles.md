# Versionierte Formatprofile

`profile-registry.json` enthält drei explizite Profile mit stabiler ID, Typ,
Titel, Version, Status, realem Erstellungsdatum der neuen Metadaten, Quelle,
Vorgänger, Eigentümer/Autor, Änderungsgrund und Inhaltshash. Die Organisation
ist unbekannt und wird als `UNKNOWN` gespeichert. Ursprung und ursprüngliche
MIT-Urheberangabe werden nicht durch eine erfundene Organisation ersetzt.

Die neue Version 0.2.0 ist zunächst ein technisch geprüfter Draft. Das
vorhandene 0.1.0-Wheel bleibt unverändert. `flowlib-legacy-v1` behält seine
Formatsemantik; `plain-v1` ist ein eigenständiges neues Profil ohne Heuristik.
Unbekannte externe Profile und JKB-Regeln werden nicht einbezogen.

`flowlib-v2` (Version 2.0.0, Vorgänger `flowlib-legacy-v1@1.0.0`) behebt
Befund B1 der Spezifikation: Wörter statt Teilzeichenketten, Kopf des
Kompositums entscheidet, Kennungen (Postleitzahl, Kontonummer, IBAN,
Steuernummer …) ohne Zahlenformat, Werttyp vor Spaltenname. Die Regeln stehen
in `formats_v2.py`; sein Implementierungshash bindet nur dieses Profil.
`package_version` steht auf `unreleased`, bis der Release-Ablauf die erste
Paketversion mit diesem Profil einträgt. Mit dem neuen Profil änderten sich
`profiles.py` und damit die Implementierungs- und Inhaltshashes der beiden
bestehenden Profile; ihre Formatsemantik ist unverändert (34 charakterisierte
Fälle, Golden-Arbeitsmappen).

`get_profile_metadata` prüft Inhalts- und Implementierungshashes. Consumer
speichern für reproduzierbare Exporte die konkrete Profilreferenz samt
Input-/Outputhash und Renderoptionen in ihrem eigenen Laufnachweis. Die
Bibliothek führt keine heimlichen Inhaltslogs. Sie benötigt keine Prompts,
Agenten, Agent-Toolrechte oder Prompt-Suche.

Technischer Review umfasst die alten 34 Formatfälle, Original-Workbookfälle,
Wert-/Style-Roundtrips, Formeleinschleusung, Limits, fehlende Dependencies und
Versionsmetadaten. Freigaben werden mit Reviewer, Datum, Version und
Artefakthash dokumentiert. Ein erfolgreicher Build ist keine fachliche
Anwendungsfreigabe. Draft-Tests erfinden keine menschliche Zustimmung.

Veröffentlichte Wheel-/sdist-/Profilversionen bleiben mit Manifest und SBOM
unveränderlich archiviert. Änderungen an Semantik erhalten neue Profil- und
Paketversionen mit Vorgängerbezug; technische Änderungen mindestens eine neue
Paketversion. Rollback wählt das frühere Artefakt. Alte Golden-Fixtures und
Source-Commits bleiben erhalten, History-Rewrite ersetzt keine Versionierung.
