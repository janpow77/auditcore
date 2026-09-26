# FlowAudit-BPMN-Erweiterung, Schema 1.1

Verbindliche Festlegung der fachlichen BPMN-Erweiterung `flowaudit` für
`auditcore_bpmn` (Python) und `@auditcore/bpmn-flowaudit` (JavaScript).
Maschinenlesbar: `packages/auditcore_bpmn/src/auditcore_bpmn/schemas/flowaudit-1.1.xsd`.
Python-Abbildung: `auditcore_bpmn.extensions` (Feldnamen englisch, XML-Namen wie hier).

## Grundsätze

- **Namensraum unverändert:** `https://flowaudit.de/bpmn/schema/1.0`, Präfix
  `flowaudit`. Die Version 1.1 steht im Attribut `schemaVersion="1.1"` von
  `flowaudit:diagrammInfo`, nicht in der URI (ein neuer Namensraum würde
  vorhandene Dateien und 1.0-Leser brechen).
- **Additiv:** 1.1 fügt nur Elemente und optionale Attribute hinzu. Jede
  1.0-Datei ist eine gültige 1.1-Datei. Leser ignorieren unbekannte Elemente
  und Attribute des Namensraums und erhalten sie beim Schreiben (Rundlauf).
- **Ort:** alle Elemente stehen in `<bpmn:extensionElements>` des jeweiligen
  BPMN-Elements, nach allen `<bpmn:documentation>`-Kindern.
  `<bpmn:documentation>` bleibt unberührt.
- **Namen:** Elemente lowerCamelCase (moddle `tagAlias: "lowerCase"`, Typ
  `Rechtsgrundlage` → `<flowaudit:rechtsgrundlage>`), Attribute unqualifiziert.
- **Werte:** Datum `YYYY-MM-DD`, Farbe `#RRGGBB`, Wahrheitswert `true`/`false`.
  Leere Werte werden nicht geschrieben. Codes sind Datenwerte (deutsch, ohne
  Umlaute), Bezeichnungen liefern die Vokabulare zweisprachig (de/en).
- **Allgemeingültig:** keine Landes-, Behörden- oder Programmnamen im Schema,
  in Katalogen oder Vorlagen. Anzeigenamen trägt `flowaudit:akteur/@anzeigename`.
- **Vertraulich markieren:** Jedes Element mit Attribut `vertraulich="true"`
  entfällt beim neutralisierenden Export.
- **Verknüpfung zu Checklisten und Vermerken nur über stabile fachliche
  Schlüssel** (KA/BK, Prüffeld, Feststellungsbezug, Register), nie über
  Datenbank- oder Element-IDs anderer Systeme.

## Übersicht

| Element | Seit | Steht an | Anzahl |
|---|---|---|---|
| `rechtsgrundlage` | 1.0 (Attribute 1.1) | Flussknoten, `diagrammInfo`, `frist` | 0..n |
| `interneNotiz` | 1.0 | Flussknoten | 0..1 |
| `notiz` | 1.0, nur lesen | wie `interneNotiz` | Altform |
| `diagrammInfo` | 1.1 | Hauptelement (s. u.) | 0..1 |
| `akteur` | 1.1 | `participant`, `lane` | 0..1 |
| `kennzeichen` | 1.1 | Flussknoten, `participant`, `lane` | 0..n |
| `pruefbezug` | 1.1 | alle Elemente, `diagrammInfo` | 0..n |
| `kontrolle` | 1.1 | Aktivitäten, Gateways | 0..n |
| `risiko` | 1.1 | alle Elemente, `diagrammInfo` | 0..n |
| `nachweis` | 1.1 | `dataObjectReference`, `dataStoreReference` (auch `dataObject`/`dataStore`) | 0..n |
| `frist` | 1.1 | Aufgaben, Zeitgeber-Ereignisse | 0..n |
| `verweis` | 1.1 | alle Elemente, `diagrammInfo` | 0..n |
| `pruefschritt` | 1.1 | Flussknoten | 0..n |
| `feststellung` | 1.1 | alle Elemente, `diagrammInfo` | 0..n |
| `quelle` | 1.1 | alle Elemente, `diagrammInfo` | 0..n |
| `esiAnforderungen` | 1.1 | `process`, `subProcess` | 0..1 |

Schreibreihenfolge in `extensionElements`: `diagrammInfo`, `akteur`,
`rechtsgrundlage`, `interneNotiz`, `kennzeichen`, `pruefbezug`, `kontrolle`,
`risiko`, `nachweis`, `frist`, `verweis`, `pruefschritt`, `feststellung`,
`quelle`, `esiAnforderungen`; fremde Erweiterungen danach, unverändert.

## `flowaudit:rechtsgrundlage`

1.0: Textinhalt (Freitext). 1.1: zusätzlich strukturierte Attribute, alle optional.

| Attribut | Bedeutung | Beispiel |
|---|---|---|
| `id` | Kennung in der Datei | `RG_1` |
| `norm` | Rechtsakt, Normalform ausgeschrieben | `Verordnung (EU) 2021/1060`, `LHO`, `VV zu § 44 LHO` |
| `artikel` | Artikelnummer (ohne „Art.“) | `73` |
| `paragraph` | §-Nummer (ohne „§“) | `44` |
| `anhang` | Anhang | `XIII` |
| `absatz` | Absatz | `2` |
| `unterabsatz` | Unterabsatz | `2` |
| `satz` | Satz | `3` |
| `buchstabe` | Buchstabe | `b` |
| `nummer` | Nummer/Ziffer | `4.2` |
| `fassung` | Fassung/Stand | `ABl. L 231 vom 30.6.2021` |
| `eli` | European Legislation Identifier | `http://data.europa.eu/eli/reg/2021/1060/oj` |
| `celex` | CELEX-Nummer | `32021R1060` |
| `url` | Fundstelle im Netz | `https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32021R1060` |
| `kurzbezeichnung` | Kurztitel | `Programmverwaltung durch die Verwaltungsbehörde` |
| `anmerkung` | Anmerkung | frei |
| `vertraulich` | vertraulich | `true` |

**Textinhalt (Pflicht beim Schreiben strukturierter Angaben):** die
**ausgeschriebene Normalform**, damit 1.0-Leser die Angabe weiter anzeigen:

- Artikel/Anhang: `Artikel {artikel} Absatz {absatz} Unterabsatz {unterabsatz} Satz {satz} Buchstabe {buchstabe} Nummer {nummer} der {norm}`
  („der Verordnung“, „der Delegierten Verordnung“, „der Richtlinie“, „des Beschlusses“);
- Paragraph: `§ {paragraph} Absatz … Satz … {norm}` (ohne Artikel);
- Verwaltungsvorschrift: `VV Nummer {nummer} zu § 44 LHO` (norm `VV zu § 44 LHO`).

Fehlende Teile entfallen. Die **Kurzform** zur Anzeige lautet
`Art. 73 Abs. 2 UAbs. 2 S. 3 Buchst. b Nr. 4 VO (EU) 2021/1060` bzw.
`§ 44 Abs. 1 S. 2 LHO`. Leser akzeptieren ein Attribut `value`, wenn der
Textinhalt leer ist (1.0).

```xml
<flowaudit:rechtsgrundlage norm="Verordnung (EU) 2021/1060" artikel="73" absatz="2" buchstabe="b"
    celex="32021R1060" eli="http://data.europa.eu/eli/reg/2021/1060/oj">Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060</flowaudit:rechtsgrundlage>
<flowaudit:rechtsgrundlage>§ 55 BHO; Art. 74 VO (EU) 2021/1060</flowaudit:rechtsgrundlage>
```

## `flowaudit:interneNotiz`

Textinhalt. Leser akzeptieren die Altform `flowaudit:notiz` und ein Attribut `value`.

## `flowaudit:diagrammInfo`

Im `extensionElements` des **Hauptelements**: `bpmn:collaboration`, sonst
erster `bpmn:process` (`bpmn:definitions` hat in der OMG-XSD kein
`extensionElements`). Leser: zuerst Kollaboration, dann Prozesse; erstes
Vorkommen gilt.

| Attribut | Bedeutung | Werte |
|---|---|---|
| `schemaVersion` | Schemaversion | `1.1` |
| `profil` | Profil-ID der Kataloge | `foerderperiode-2021-2027` (Standard, wenn leer) |
| `titel`, `untertitel` | Titel | frei |
| `prozessverantwortlich` | prozessverantwortliche Stelle | frei |
| `prozesstyp` | Prozesstyp | frei |
| `version` | fachliche Version | frei |
| `status` | Bearbeitungsstand | `entwurf` \| `in_pruefung` \| `freigegeben` \| `archiviert` |
| `gueltigAb`, `gueltigBis` | Gültigkeit | Datum |
| `autor` | Autor (Person) | frei |
| `freigegebenDurch`, `freigegebenAm` | Freigabe | frei, Datum |
| `kopfzeilenfarbe`, `kopfzeilenTextfarbe` | Kopfzeile | `#RRGGBB` (Altmodell `#1976d2`/`#ffffff`) |
| `foerderperiode` | Förderperiode | `2014-2020` \| `2021-2027` \| `2028-2034` (erweiterbar, Muster `JJJJ-JJJJ`) |
| `programm` | Programmname | frei |
| `cci` | CCI-Nummer | frei |
| `vertraulichkeit` | Vertraulichkeitsstufe | `offen` \| `intern` \| `vs_nfd` |
| `variante` | Soll/Ist | `soll` (Beschreibung des VKS) \| `ist` (Durchlauftest) |
| `bezugDiagramm` | bei `ist`: ID des Soll-Diagramms in der Sammlung | frei |
| `vksStichtag` | Stichtag des VKS-Stands | Datum |

Kindelemente in dieser Reihenfolge: `beschreibung` (0..1, Text),
`schlagwort` (0..n, Text), `fonds` (0..n, Code: `efre`, `esf_plus`, `kf`,
`jtf`, `emfaf`, `amif`, `isf`, `bmvi`, `interreg`; 2014–2020 zusätzlich `esf`,
`emff`, `eler`), `rechtsgrundlage`, `pruefbezug`, `risiko`, `feststellung`,
`quelle`, `verweis` (je 0..n).

```xml
<bpmn:collaboration id="Collaboration_1">
  <bpmn:extensionElements>
    <flowaudit:diagrammInfo schemaVersion="1.1" profil="foerderperiode-2021-2027"
        titel="Verwaltungskontrolle" status="freigegeben" foerderperiode="2021-2027"
        gueltigAb="2026-01-01" freigegebenDurch="Referatsleitung" freigegebenAm="2025-12-15"
        vertraulichkeit="intern" variante="soll" vksStichtag="2026-06-30">
      <flowaudit:beschreibung>Ablauf der VerwK.</flowaudit:beschreibung>
      <flowaudit:schlagwort>VerwK</flowaudit:schlagwort>
      <flowaudit:fonds>efre</flowaudit:fonds>
      <flowaudit:pruefbezug ka="4" bk="4.1" art="systempruefung"/>
    </flowaudit:diagrammInfo>
  </bpmn:extensionElements>
</bpmn:collaboration>
```

**Freigabe und Revisionssicherheit:** Der SHA-256 des freigegebenen Stands
steht **nicht** im XML (er würde sich selbst verändern), sondern in der
Diagrammsammlung (`approvals`: Version, SHA-256 über die UTF-8-Bytes des
gespeicherten XML, Stichtag, Freigabe am/durch). Eine freigegebene Version
ist unveränderlich; Änderungen erfordern eine neue Version.

## `flowaudit:akteur`

| Attribut | Pflicht | Werte |
|---|---|---|
| `rolle` | ja | Rollencode (Katalog des Profils, erweiterbar über `custom_roles`) |
| `anzeigename` | nein | Name der Stelle im Programm |

Standardkatalog (Periodenbindung in Klammern): `vb` Verwaltungsbehörde,
`zgs` Zwischengeschaltete Stelle, `rfs` Stelle mit Rechnungsführungsfunktion
(ab 2021–2027), `bb` Bescheinigungsbehörde (bis 2014–2020), `pb`
Prüfbehörde, `pbs` programmbeteiligte Stelle, `kom` Europäische Kommission,
`beg` Begünstigte, `bga` Begleitausschuss, `gs` Gemeinsames Sekretariat
(Interreg), `gdp` Gruppe von Prüfern (Interreg), `fb`
Fachbehörde/Bewilligungsstelle, `ftd` fachtechnische Dienststelle, `gut`
Gutachter/Sachverständige, `gre` Gremium, `fr` Fachreferat, `ds`
Datenschutz, `it` IT-System, `sonstige`.

## `flowaudit:kennzeichen`

| Attribut | Pflicht | Werte |
|---|---|---|
| `typ` | ja | siehe unten |
| `text` | nein | Hinweistext |

Typen: `rechtsgrundlage`, `pruefpunkt`, `frist`, `vier_augen`, `dokument`,
`risiko`, `system`, `zahlung`, `bewilligung`, `schluesselkontrolle`,
`checkliste`, `bescheid`, `stellungnahme`, `gremium`, `interessenkonflikt`,
`veroeffentlichung` sowie befundbezogen `feststellung`,
`feststellung_formell`, `feststellung_finanziell`, `offener_nachweis`,
`ohne_befund`, `soll_ohne_regelung`.

**Farbsemantik:** Farbe wird nicht als Bedeutung gespeichert, sondern aus
Kennzeichen abgeleitet (Vorrang in dieser Reihenfolge):
`feststellung_finanziell`/`feststellung_formell`/`feststellung` →
Füllung `#fce8e6`, Rand `#b3261e`; `soll_ohne_regelung` → `#ffe0e0`/`#cc0000`;
`offener_nachweis` → `#bbdefb`/`#0d47a1`; `ohne_befund` → `#c8e6c9`/`#1b5e20`.
Beim Import vorhandener Diagramme werden diese Farben (und `#ffcdd2`/`#b71c1c`)
als **Vorschlag** in Kennzeichen zurückübersetzt.

## `flowaudit:pruefbezug`

| Attribut | Pflicht | Werte |
|---|---|---|
| `ka` | ja | Nummer der Kernanforderung im **KA-Katalog des Profils** (2021–2027: 1–15, Anhang XI VO (EU) 2021/1060; 2014–2020: 1–18, Anhang IV Delegierte VO (EU) Nr. 480/2014) |
| `bk` | nein | Bewertungskriterium, beginnt mit `{ka}.` (z. B. `2.3`) |
| `art` | nein | `verwk` \| `systempruefung` \| `vorhabenpruefung` \| `rechnungslegungspruefung` |
| `anmerkung` | nein | frei |

Bewertungskriterien stehen in keinem der Rechtstexte; die Anwendung speist
sie in das Profil ein (`Profile.with_assessment_criteria`).

## `flowaudit:kontrolle`

| Attribut/Kind | Werte |
|---|---|
| `id` | Kennung (Ziel von `risiko/@kontrollen`, `pruefschritt/@kontrolle`) |
| `bezeichnung` | frei |
| `schluesselkontrolle` | `true`/`false` |
| `art` | `praeventiv` \| `aufdeckend` |
| `durchfuehrung` | `manuell` \| `it_gestuetzt` \| `automatisiert` |
| `haeufigkeit` | frei (z. B. `je Antrag`) |
| `nachweis` | Dokument als Nachweis der Durchführung |
| `verantwortlich` | Rollencode |
| `beschreibung` (Kind) | Text |

## `flowaudit:risiko`

`id`, `bezeichnung`, `kategorie` (`allgemein` \| `betrug` \|
`interessenkonflikt` \| `doppelfinanzierung`), `inhaerent`, `kontrollrisiko`,
`restrisiko` (je `niedrig` \| `mittel` \| `hoch`), `kontrollen` (IDs durch
Leerzeichen getrennt), Kind `beschreibung`. Grundlage der
Risiko-Kontroll-Matrix (Art. 74 Abs. 1 Buchst. c VO (EU) 2021/1060).

## `flowaudit:nachweis` (Prüfpfad)

`dokumentart`, `aufbewahrungsort`, `itSystem`, `aufbewahrungsfrist`
(z. B. „fünf Jahre ab dem 31. Dezember des Jahres der letzten Zahlung
(Artikel 82 Absatz 1)“), `anmerkung`.

## `flowaudit:frist`

`wert` (z. B. `80`), `einheit` (`tage` \| `arbeitstage` \| `wochen` \|
`monate` \| `jahre`), `bezug` (z. B. „ab Einreichung des
Auszahlungsantrags“), `anmerkung`, Kinder `rechtsgrundlage` (0..n).

```xml
<flowaudit:frist wert="80" einheit="tage" bezug="ab Einreichung des Auszahlungsantrags">
  <flowaudit:rechtsgrundlage norm="Verordnung (EU) 2021/1060" artikel="74" absatz="1" buchstabe="b">Artikel 74 Absatz 1 Buchstabe b der Verordnung (EU) 2021/1060</flowaudit:rechtsgrundlage>
</flowaudit:frist>
```

## `flowaudit:verweis`

| Attribut | Pflicht | Werte |
|---|---|---|
| `art` | ja | `prueffeld` \| `feststellung_ref` \| `register` |
| `schluessel` | ja | z. B. `3.21`, `T15 F1`, `A1` |
| `dokument` | nein | z. B. Name der Checkliste |

## `flowaudit:pruefschritt` (Durchlauf- und Kontrolltest)

`id`, `fall` (Fall/Vorhaben), `beleg`, `ergebnis` (`erfuellt` \|
`nicht_erfuellt` \| `nicht_anwendbar` \| `offen`), `datum`, `pruefer`
(Person), `kontrolle` (ID einer Kontrolle für den Kontrolltest),
`stichprobe`, `grundgesamtheit` (ganze Zahlen), Kind `bemerkung`.

## `flowaudit:feststellung`

`id`, `kennung` (z. B. `T15 F1`), `art` (`formell` \| `finanziell`),
`einstufung` (`gering` \| `mittel` \| `schwerwiegend`), `ka`, `bk`, `frist`
(Datum), `status` (`offen` \| `in_umsetzung` \| `umgesetzt` \|
`nicht_umgesetzt` \| `entfallen`), Kinder `beschreibung`, `empfehlung`.

## `flowaudit:quelle`

`art` (`verfahrenshandbuch` \| `interview` \| `durchlauftest` \|
`arbeitspapier` \| `sonstige`), `fundstelle`, `datum`, `referenz`
(Arbeitspapier), Textinhalt.

## `flowaudit:esiAnforderungen`

`profil`; Kinder `esiAnforderung` mit `code` und Kindern `kriterium` (Text).
Altbestand `esiProfile`/`esiCoreRequirements="KA1:K1,K2;KA2"` am Prozess
wird gelesen, wenn das Element fehlt.

## Weiter gelesene Alt-Attribute (FlowStat, ohne Namensraum)

`processOwner`, `processDepartment`, `processType`,
`resourcesPersonnel`/`resource`, `resourcesSystems`, `resourcesDocuments`,
`durationEstimated`/`duration`/`durationMinutes`, `durationUnit`,
`personnelGrade`, `personnelCount`/`personnel_count`/`personnel`,
`costEstimate`/`cost`, `effortPersonDays`, `frequency`/`frequencyPerYear`
an Aufgaben; `esiProfile`, `esiCoreRequirements` an Prozessen.

## moddle-Deskriptor (Vorgabe für `@auditcore/bpmn-flowaudit`)

`name: "FlowAudit"`, `uri: "https://flowaudit.de/bpmn/schema/1.0"`,
`prefix: "flowaudit"`, `xml: { tagAlias: "lowerCase" }`; alle Typen
`superClass: ["Element"]`, alle Eigenschaften `String` (Zahlen und Daten
prüfen die Regeln, nicht moddle).

| Typ | Eigenschaften (`isAttr`, sofern nicht anders) |
|---|---|
| `Rechtsgrundlage` | `value` (`isBody`), `id`, `norm`, `artikel`, `paragraph`, `anhang`, `absatz`, `unterabsatz`, `satz`, `buchstabe`, `nummer`, `fassung`, `eli`, `celex`, `url`, `kurzbezeichnung`, `anmerkung`, `vertraulich` |
| `InterneNotiz`, `Notiz`, `Beschreibung`, `Empfehlung`, `Bemerkung`, `Schlagwort`, `Fonds`, `Kriterium` | `value` (`isBody`) |
| `DiagrammInfo` | alle Attribute der Tabelle oben; `beschreibung` (Typ `Beschreibung`); `schlagwoerter` (`Schlagwort`, `isMany`); `fonds` (`Fonds`, `isMany`); `rechtsgrundlagen`, `pruefbezuege`, `risiken`, `feststellungen`, `quellen`, `verweise` (je `isMany`) |
| `Akteur` | `rolle`, `anzeigename` |
| `Kennzeichen` | `typ`, `text`, `vertraulich` |
| `Pruefbezug` | `ka`, `bk`, `art`, `anmerkung`, `vertraulich` |
| `Kontrolle` | `id`, `bezeichnung`, `schluesselkontrolle`, `art`, `durchfuehrung`, `haeufigkeit`, `nachweis`, `verantwortlich`, `vertraulich`; `beschreibung` (`Beschreibung`) |
| `Risiko` | `id`, `bezeichnung`, `kategorie`, `inhaerent`, `kontrollrisiko`, `restrisiko`, `kontrollen`, `vertraulich`; `beschreibung` |
| `Nachweis` | `dokumentart`, `aufbewahrungsort`, `itSystem`, `aufbewahrungsfrist`, `anmerkung`, `vertraulich` |
| `Frist` | `wert`, `einheit`, `bezug`, `anmerkung`; `rechtsgrundlagen` (`Rechtsgrundlage`, `isMany`) |
| `Verweis` | `art`, `schluessel`, `dokument`, `vertraulich` |
| `Pruefschritt` | `id`, `fall`, `beleg`, `ergebnis`, `datum`, `pruefer`, `kontrolle`, `stichprobe`, `grundgesamtheit`, `vertraulich`; `bemerkung` (`Bemerkung`) |
| `Feststellung` | `id`, `kennung`, `art`, `einstufung`, `ka`, `bk`, `frist`, `status`, `vertraulich`; `beschreibung`, `empfehlung` (`Empfehlung`) |
| `Quelle` | `art`, `fundstelle`, `datum`, `referenz`, `vertraulich`; `value` (`isBody`) |
| `EsiAnforderungen` | `profil`; `anforderungen` (`EsiAnforderung`, `isMany`) |
| `EsiAnforderung` | `code`; `kriterien` (`Kriterium`, `isMany`) |

## Prüfregeln zum Schema

Vollständiger Katalog mit IDs, Schweregrad und Texten (de/en):
`packages/auditcore_bpmn/docs/rules.md`. Auszug: `BPMN-F001` Aufgabe ohne
Rechtsgrundlage (Hinweis), `BPMN-F020` Pool/Lane ohne Akteur-Rolle (Hinweis),
`BPMN-F022` Rolle nicht für die Förderperiode vorgesehen (Hinweis),
`BPMN-F023` KA nicht im Katalog des Profils (Fehler), `BPMN-F024` BK passt
nicht zur KA (Fehler), `BPMN-P001` Kontrolle ohne Nachweis, `BPMN-P002`
Datenobjekt ohne Aufbewahrungsort, `BPMN-P003` Frist ohne Rechtsgrundlage,
`BPMN-P004` Schlüsselkontrolle ohne Test, `BPMN-FT01`–`FT05`
Funktionstrennung (Regeln im Profil).
