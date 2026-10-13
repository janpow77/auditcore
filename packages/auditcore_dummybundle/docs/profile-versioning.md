# Vorlagenprofile: Versionierung und Freigabe

Die elf Vorlagenprofile liegen als Daten unter
`src/auditcore_dummybundle/template_data/`. Jedes Profil trägt eine stabile
Kennung (`artifact_id`), Version, Stand, Inhaltshash und einen
Freigabevermerk (`review`).

## Inhaltshash

`content_hash` ist der SHA-256 über die kanonische JSON-Form
(`auditcore_common.hashing.canonical_sha256`) von Kennung, Version, Titel,
Zweck, Rechtsgrundlage und Tabellen. `templates()` prüft ihn beim Laden und
weist ein verändertes Profil mit `profile_hash` ab. Quellenangaben und
offene Punkte sind Erläuterung und gehen nicht in den Hash ein.

## Freigabe vom 13.10.2026

Der Rechteinhaber und Auftraggeber (Repository-Inhaber janpow77) hat am
13.10.2026 die elf Vorlagenprofile von `auditcore_dummybundle` 0.1.0
freigegeben: V0 bis V9 und N1, jeweils in der Fassung des im Profil
genannten Inhaltshashes. Stand der Profile: „Freigegeben“,
`review.human_release_approval`: `GRANTED`. Die Hashes stehen zusätzlich in
`provenance.json` unter `profile_release`.

Die Freigabe gilt nicht für

- die Profile von `auditcore_dummygenerator`: Sie bleiben „Draft“ mit
  `NOT_GRANTED`; an ihnen wurde nichts geändert;
- Texte Dritter: Titel, Kopffelder und Spaltenköpfe der Vorlagen V5 und V6
  stammen aus den Anhängen XXIII und XXIV der Verordnung (EU) 2021/1060 und
  sind Unionsrecht. Die beiden Profile weisen das unter `review.third_party`
  aus.

Die Freigabe ist eine Entscheidung über die Profile. Sie ersetzt keinen
Prüfbericht und sagt nichts über die Auslieferung einer Anwendung.

## Änderungen

Ein freigegebenes Profil wird nicht mit anderem Inhalt ersetzt. Jede
fachliche Änderung – Spalte, Kopf, Rechenbezug, Titel – ergibt eine neue
Profil- und Paketversion mit neuem Inhaltshash und braucht eine neue
Freigabe; bis dahin steht das geänderte Profil nicht auf „Freigegeben“.
Der Schalter `public` steuert nur die Sichtbarkeit und ist nicht Teil des
Hashes.
