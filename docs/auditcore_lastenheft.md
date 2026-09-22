# LASTENHEFT / MASTER IMPLEMENTATION SPECIFICATION

## AuditCore Platform
### Repository-Inventur, KIRA-RAG-Wissensbasis, gemeinsame Fachbibliothek, Refactoring, Qualitätsprüfung und APT-Deployment

**Version:** 1.5  
**Stand:** September 2026  
**Zielplattform:** Python >= 3.11  
**Primärsysteme:** GitHub, KIRA RAG, Graphify  
**Kernkomponenten:** eine Fachbibliothek `auditcore` und vier Werkzeugkomponenten `quality`, `consolidator`, `apprefactor`, `deployer` im selben Repository und Releasezyklus

---

# 0. Verwendung dieses Dokuments durch Codex

Dieses Dokument ist nicht nur eine Beschreibung, sondern ein verbindlicher Implementierungsauftrag.

Codex soll dieses Dokument vollständig von oben nach unten abarbeiten.

## 0.1 Arbeitsweise

Codex soll:

1. den aktuellen Repository- und Git-Kontext analysieren,
2. die bestehende Struktur respektieren,
3. die hier beschriebenen Komponenten vollständig implementieren,
4. vorhandene Funktionen wiederverwenden,
5. fehlende Komponenten ergänzen,
6. Tests ausführen,
7. Fehler selbstständig beheben,
8. Quality Gates erneut ausführen,
9. erst nach erfolgreicher Prüfung abschließen.

Ein bloßes Erstellen von Gerüsten, TODO-Dateien oder Platzhaltern gilt nicht als Fertigstellung.

## 0.2 Keine erfundenen Prüfergebnisse

Codex darf niemals behaupten, dass:

- Tests bestanden haben,
- ein Tool ausgeführt wurde,
- ein Repository untersucht wurde,
- KIRA synchronisiert wurde,
- Graphify analysiert wurde,

wenn dies tatsächlich nicht erfolgt ist.

Wenn ein Tool technisch nicht verfügbar ist, ist dies ausdrücklich mit:

`NOT_EXECUTED`

oder

`NOT_CONFIGURED`

zu dokumentieren.

## 0.3 Keine destruktiven Git-Aktionen

Nicht zulässig:

- Force Push
- History Rewrite
- ungefragtes Löschen von Branches
- ungefragtes Überschreiben fremder Änderungen
- ungefragtes Löschen bestehender Fachlogik

Bevorzuge kleine, logisch getrennte Änderungen und Commits.

---

# 1. Ausgangssituation

Es existieren mehrere Softwareprojekte und GitHub-Repositories mit teilweise überlappender Funktionalität.

Dazu gehören insbesondere Anwendungen und Projekte aus den Bereichen:

- Audit und Prüfung
- Fördermittelkontrolle
- Zuwendungsrecht
- Vergabeprüfung
- Risikoanalyse
- Stichproben
- Dokumentenanalyse
- Berichterstellung
- Office-Automatisierung
- Datenanalyse
- Checklisten
- KI-gestützte Recherche
- Verwaltungsverfahren

Im Laufe der Entwicklung wurden gleiche oder ähnliche fachliche und technische Funktionen mehrfach implementiert.

Dies führt langfristig zu Risiken hinsichtlich:

- redundanter Entwicklung
- unterschiedlicher Implementierungen
- Wartbarkeit
- Testbarkeit
- Nachvollziehbarkeit
- Wiederverwendbarkeit
- Versionsmanagement
- technischer Schulden

---

# 2. Gesamtziel

Es soll eine zentrale, wiederverwendbare Bibliotheks- und Wissensarchitektur entstehen.

Das System soll:

1. alle relevanten GitHub-Repositories des authentifizierten Benutzers inventarisieren,
2. relevante Code-Symbole erfassen,
3. semantisch ähnliche Implementierungen erkennen,
4. Abhängigkeiten analysieren,
5. gemeinsame Bibliothekskandidaten erkennen,
6. gemeinsame Fachlogik nach `auditcore` oder geeignete weitere Bibliotheken überführen,
7. bestehende Fachanwendungen kontrolliert auf gemeinsame Bibliotheken migrieren,
8. technische und fachliche Regressionen verhindern,
9. Qualitätsprüfungen automatisieren,
10. das gewonnene Wissen dauerhaft in KIRA RAG speichern,
11. spätere Änderungen inkrementell statt vollständig neu analysieren.


---

# 2A. Präzisierter Primärauftrag der Plattform

Die Repository-Inventur und KIRA-Wissensbasis sind Mittel zum Zweck und nicht das eigentliche Endprodukt.

Der Primärauftrag lautet:

```text
BESTEHENDE REPOSITORIES ANALYSIEREN
        ↓
WIEDERVERWENDBARE LOGIK IDENTIFIZIEREN
        ↓
GEMEINSAME BIBLIOTHEKEN ERSTELLEN
        ↓
BESTEHENDE REPOSITORIES ENTLASTEN
        ↓
FACHANWENDUNGEN AUF GEMEINSAME BIBLIOTHEKEN MIGRIEREN
        ↓
ANWENDUNGEN TECHNISCH OPTIMIEREN
        ↓
TESTEN UND QUALITÄT SICHERN
        ↓
ANWENDUNGEN ALS DEBIAN-/APT-PAKETE BAUEN
        ↓
REPRODUZIERBAR AUF ZIELSERVERN DEPLOYEN
```

Die Plattform ist daher nicht nur ein Inventarisierungswerkzeug.

Sie ist ein Werkzeug zur:

- Konsolidierung,
- Modularisierung,
- Entkopplung,
- Modernisierung,
- Qualitätssteigerung,
- Wiederverwendung,
- Paketierung,
- Bereitstellung

der bestehenden Softwarelandschaft.

---

# 2B. Zielzustand bestehender Fachanwendungen

Bestehende Fachanwendungen sollen nach der Konsolidierung möglichst wenig duplizierte Fachlogik enthalten.

Eine Anwendung soll im Zielbild im Wesentlichen bestehen aus:

```text
Fachanwendung
├── UI
├── API / Application Layer
├── Authentifizierung / Autorisierung
├── anwendungsspezifische Orchestrierung
├── Datenpersistenz
└── Shared Libraries
    ├── auditcore
    └── ggf. weitere gemeinsame Bibliotheken
```

Fachlogik, die von mehreren Anwendungen verwendet wird oder sinnvoll wiederverwendbar ist, soll nicht dauerhaft in einzelnen Anwendungen verbleiben.

---

# 2C. Refactoring- und Optimierungsziel

Der Consolidator soll nicht nur Code verschieben.

Er soll nach gesicherter fachlicher Gleichheit auch prüfen, ob die bestehende Implementierung verbessert werden kann.

Optimierungsziele sind insbesondere:

- klare Modulgrenzen,
- kleinere öffentliche APIs,
- bessere Typisierung,
- weniger Duplikate,
- weniger Frameworkkopplung,
- weniger Datenbankkopplung,
- bessere Testbarkeit,
- verständlichere Fehlerbehandlung,
- geringere unnötige Abhängigkeiten,
- bessere Performance,
- geringerer Speicherverbrauch,
- bessere Wartbarkeit,
- bessere Dokumentation.

Optimierungen dürfen keine unbemerkte fachliche Bedeutungsänderung verursachen.

Vor und nach der Optimierung müssen Regressionstests durchgeführt werden.

---

# 2D. Bibliotheksstrategie

`auditcore` ist die primäre gemeinsame Fachbibliothek.

Weitere Bibliotheken dürfen nur entstehen, wenn dies aufgrund einer klaren technischen oder fachlichen Abgrenzung sinnvoll ist.

Beispielsweise:

```text
auditcore
auditcore-documents
auditcore-office
auditcore-reporting
auditcore-data
```

Es gilt:

```text
SO FEW SHARED LIBRARIES AS POSSIBLE
AS MANY AS NECESSARY
```

Die Bibliothekslandschaft soll übersichtlich bleiben.


---

# 3. Grundarchitektur

Die Plattform besteht aus **einer Fachbibliothek und vier logisch getrennten Werkzeugkomponenten** im selben Repository und zunächst im selben Python-Projekt bzw. Releasezyklus:

```text
auditcore
    Fachliche, frameworkunabhängige Kernbibliothek

auditcore.tools.quality
    Deterministische Qualitäts- und Architekturprüfung

auditcore.tools.consolidator
    Repository-Inventur, Analyse, KIRA-/Graphify-Auswertung,
    Bibliothekskandidaten und Konsolidierungsplanung

auditcore.tools.apprefactor
    Refactoring, Entkopplung, technische Optimierung und
    Migration bestehender Fachanwendungen auf Shared Libraries

auditcore.tools.deployer
    Paketierung, Release-Build, Debian-/APT-Erstellung,
    Installationsprüfung und Deployment kompletter Anwendungen
```

Die Verantwortlichkeiten sind strikt zu trennen, ohne daraus von Beginn an fünf eigenständig versionierte Pakete zu machen:

```text
auditcore
    WAS ist gemeinsame Fachlogik?

quality
    IST der Code technisch und architektonisch zulässig?

consolidator
    WAS existiert bereits, WAS ist gemeinsam und
    WAS soll wohin konsolidiert werden?

apprefactor
    WIE wird eine konkrete Fachanwendung auf Shared Libraries
    umgestellt, entschlackt, entkoppelt und technisch optimiert?

deployer
    WIE wird eine fertige Anwendung gebaut, paketiert,
    installiert, aktualisiert und ausgeliefert?
```

## Paketierungsgrundsatz

Standardmäßig gilt:

```text
ONE REPOSITORY
ONE PYTHON PROJECT
ONE RELEASE CYCLE
ONE CORE LIBRARY
FOUR TOOL COMPONENTS
```

Erst wenn eine Werkzeugkomponente später einen klar unabhängigen Releasezyklus, deutlich andere Laufzeitabhängigkeiten oder einen eigenständigen Nutzungsfall entwickelt, darf eine physische Pakettrennung vorgeschlagen werden.

Eine Trennung ist zunächst **logisch**, nicht zwingend **physisch**.

## Dependency-Richtung

Die Fachbibliothek `auditcore` darf niemals von den Werkzeugkomponenten abhängen.

```text
auditcore
    ✗ quality
    ✗ consolidator
    ✗ apprefactor
    ✗ deployer
```

Die Tools dürfen die öffentlichen Modelle und APIs von `auditcore` verwenden, jedoch nicht umgekehrt.



Ergänzende Systeme:

```text
GitHub
    Primärquelle für tatsächlichen Quellcode

KIRA RAG
    Persistenter semantischer Wissens- und Inventarindex

Graphify
    Strukturelle Analyse von Code-Abhängigkeiten

LLM
    Semantische Analyse, Vergleich und Vorschlagserstellung
```

---

# 4. Leitprinzipien

Verbindliche Grundsätze:

```text
GITHUB BEFORE KIRA

GITHUB = CODE SOURCE OF TRUTH

KIRA = KNOWLEDGE SOURCE

KIRA REMEMBERS WHAT WAS LEARNED

INVENTORY BEFORE CONSOLIDATION

REUSE BEFORE REWRITE

CHARACTERIZE BEFORE REFACTOR

EVIDENCE BEFORE ASSUMPTION

NO SILENT SEMANTIC CHANGES

NO SILENT API BREAKS

TEST LIBRARY AND CONSUMERS

AUDITABILITY OVER CLEVERNESS

PYTHON ENFORCES WORKFLOW

POLICIES ENFORCE BOUNDARIES

BIBQUALITY ENFORCES TECHNICAL QUALITY

LLM PROVIDES SEMANTIC ANALYSIS

HUMAN DECIDES DOMAIN POLICY
```


## 4.1 Verbindliche externe Policy-Quelle

Das Repository:

```text
janpow77/verwaltung-app-framework
```

ist die verbindliche allgemeine Quelle für übergreifende Anforderungen an:

- IT-Sicherheit,
- Datenschutz,
- Architektur,
- Betrieb,
- Entwicklungsstandards,
- Authentifizierung und Autorisierung,
- Logging und Nachvollziehbarkeit,
- Secret Handling,
- Mandanten- und Berechtigungstrennung,
- Deployment- und Betriebsanforderungen.

Diese Vorgaben werden **nicht als zweite unabhängige Wahrheit nach `auditcore` kopiert**.

Stattdessen muss `auditcore` einen `PolicyProvider` bzw. `FrameworkPolicyProvider` bereitstellen, der die jeweils gültigen Anforderungen aus `verwaltung-app-framework` einliest und mit Provenienz versieht.

Mindestens zu speichern:

```text
source_repository
source_path
requirement_id
commit_sha
classification
scope
```

Abgeleitete technische Prüfungen dürfen in `auditcore.tools.quality` implementiert werden, müssen aber auf die ursprüngliche Vorgabe im Framework-Repository zurückverweisen.

Es gilt:

```text
verwaltung-app-framework
    = POLICY / SECURITY SOURCE OF TRUTH

auditcore
    = SHARED DOMAIN LOGIC + EXECUTABLE TOOLING
```

Vor folgenden Schritten müssen anwendbare Framework-Policies ausgewertet werden:

- Shared-Library-Erstellung,
- Architekturänderung,
- Fachanwendungs-Refactoring,
- Dependency-Änderung,
- Security-relevante Optimierung,
- Paketierung,
- Deployment.


---


# 4.2 Policy-Evaluation-Gate für Framework-Anforderungen

Die Anforderungen aus `janpow77/verwaltung-app-framework` dürfen nicht pauschal und ungefiltert auf jedes Repository oder jede Anwendung angewendet werden.

Die verbindliche Anwendbarkeitslogik ergibt sich insbesondere aus:

```text
AGENTS.md
docs/anforderungen.md
docs/verbindlichkeit.md
docs/pruefkatalog.md
docs/security/*
docs/standards.md
docs/standards-register.json
```

`docs/verbindlichkeit.md` ist für die Einstufung des Umfangs besonders zu berücksichtigen.

Es gilt ausdrücklich:

```text
MUSS
    = für jedes Projekt zu bearbeiten;
      Umsetzung ODER begründete Abweichung mit zuständiger Entscheidung

BEDINGT
    = Auslöser prüfen;
      nur bei gegebenem Auslöser wird die Anforderung zum MUSS

SOLL
    = empfohlene Ausgestaltung;
      Alternative und Folgen dokumentieren
```

Daraus folgt:

```text
MUSS != identische technische Umsetzung in jedem Projekt
```

und:

```text
BEDINGT != automatisch verpflichtend
```

Vor der Erzeugung eines Security-, Architektur- oder Compliance-Fehlers muss deshalb immer zuerst die Anwendbarkeit bestimmt werden.

---

# 4.3 ApplicabilityContext

Für jedes analysierte Repository beziehungsweise jede Fachanwendung ist zunächst ein strukturierter `ApplicabilityContext` zu erzeugen.

Dieser muss mindestens erfassen:

```text
artifact_type
    library
    prototype
    application
    service
    deployment_package

data_space
    single_project
    multi_tenant
    shared

user_model
    no_users
    single_user
    multi_user
    external_users

personal_data
    none
    possible
    yes
    unknown

binding_decisions
    none
    drafts_only
    yes

workflow
    calculation_only
    simple_crud
    procedural
    state_machine

authentication
    none
    local
    oidc
    other

uploads
    false
    true

external_interfaces
    false
    true

ai_usage
    none
    local
    external_provider
    multiple_providers
    byok

deployment_target
    prototype
    internal_test
    pilot
    production

protection_need
    normal
    high
    very_high
    unknown

interactive_workspace
    false
    true

real_data_for_test_generation
    false
    true
```

Erweiterungen sind zulässig.

Unbekannte Werte dürfen nicht stillschweigend als `false` interpretiert werden.

Status:

```text
UNKNOWN
```

ist ausdrücklich zulässig.

---

# 4.4 Framework-Anforderungen F-01 bis F-18

Der Policy Provider muss die im Framework beschriebenen Anforderungen F-01 bis F-18 berücksichtigen.

Insbesondere darf die jeweilige technische Konkretisierung erst nach Prüfung des Auslösers erfolgen.

Beispiele:

```text
F-01
Mehrmandantenbetrieb
    → Trennung in API, Diensten, Datenhaltung und Export

Einzelprojekt
    → klar begrenzter Datenraum
```

```text
F-06
verbindliche Freigaben
    → Vier-Augen-Prinzip, Versionsschutz,
      zurechenbare Entscheidung

reine Entwurfsspeicherung
    → keine automatische Pflicht zum Vier-Augen-Prinzip
```

```text
F-07
Authentifizierung / Uploads / externe Schnittstellen / KI
    → zusätzliche Sicherheitsprüfungen
```

```text
F-08
Produktivbetrieb
    → Wartung, Sicherung, Wiederherstellung und Übergabe

Prototyp
    → offene Betriebsfragen müssen sichtbar sein,
      sind aber nicht automatisch ein Implementierungsfehler
```

```text
F-14
mehrere KI-Provider / BYOK / persönliche Endpunkte
    → Providervertrag, Secret Store,
      Datenklassen und Provider-Protokollierung
```

```text
F-17
Analyse / Simulation / ML / KI / Notebook-Ausführung
    → Reproduzierbarkeit und gegebenenfalls Workspace-Isolation
```

Die aktuelle Fassung des Framework-Repositories ist jeweils maßgeblich.

Keine Liste in `auditcore` darf eine spätere Änderung im Framework dauerhaft überschreiben.

---

# 4.5 Security- und Anwendungprofile

Zur technischen Vereinfachung darf `auditcore` aus dem `ApplicabilityContext` ein oder mehrere Profile ableiten.

Diese Profile sind **keine neue Source of Truth**, sondern nur eine ausführbare Gruppierung anwendbarer Framework-Anforderungen.

Mindestens vorzusehen:

```text
LIBRARY
PROTOTYPE
INTERNAL_APP
PROCEDURAL_APP
AI_ENABLED
HIGH_PROTECTION
```

Profile dürfen kombiniert werden.

Beispiel:

```text
regulierung

Profiles:
    INTERNAL_APP
    PROCEDURAL_APP
```

Eine KI-Anwendung kann zusätzlich erhalten:

```text
AI_ENABLED
```

Eine Anwendung mit erhöhtem Schutzbedarf zusätzlich:

```text
HIGH_PROTECTION
```

---

# 4.6 Profil `LIBRARY`

Für reine Python-Bibliotheken wie `auditcore` sind insbesondere relevant:

```text
Secrets
Dependencies
Supply Chain
SBOM
reproduzierbarer Build
sichere Deserialisierung
statische Analyse
Typprüfung
Tests
Provenienz
Versionierung
keine internen Credentials
keine unnötigen internen Daten
```

Nicht automatisch anwendbar sind beispielsweise:

```text
OIDC
Benutzerrollen
Vier-Augen-Prinzip
Mandantentrennung
CSP
HSTS
Session Management
```

sofern die Bibliothek diese Funktionen nicht selbst implementiert.

Ein Quality Gate darf daher `auditcore` nicht allein wegen fehlender Benutzeranmeldung oder fehlender Mandantentrennung als fehlerhaft bewerten.

---

# 4.7 Profil `PROTOTYPE`

Bei einem ausdrücklich als Prototyp oder Demonstrator klassifizierten System gelten weiterhin Basissicherheitsanforderungen.

Es ist aber zulässig, dass bestimmte Betriebsfragen offen bleiben, sofern sie:

- sichtbar,
- dokumentiert,
- nicht fälschlich als produktionsreif dargestellt

werden.

Vor einem Übergang zu Pilot- oder Produktivbetrieb muss die Policy-Evaluation erneut durchgeführt werden.

---

# 4.8 Profil `INTERNAL_APP`

Bei internen Fachanwendungen sind je nach Anwendbarkeit insbesondere zu prüfen:

```text
Authentifizierung
serverseitige Autorisierung
Rollen und Rechte
Logging
Fehlerbehandlung
Secret Handling
Datenschutz
Uploads
Export
Backup / Restore
Security Header
Dependency Security
```

Nicht jede interne Anwendung benötigt automatisch Mehrmandantentrennung oder Vier-Augen-Freigaben.

---

# 4.9 Profil `PROCEDURAL_APP`

Bei Anwendungen mit verbindlichen Entscheidungen, Freigaben oder fachlichem Zustandsmodell sind zusätzlich insbesondere zu prüfen:

```text
fachlicher Lebenszyklus
zulässige Zustandsübergänge
Chronologie
Versionsschutz
zurechenbare Entscheidungen
Vier-Augen-Prinzip, wenn F-06 ausgelöst wird
Rechteentzug
Nachweisführung
Integrität
```

Dieses Profil ist insbesondere für Verwaltungs- und Verfahrensanwendungen relevant.

---

# 4.10 Profil `AI_ENABLED`

Bei KI-Funktionen sind zusätzlich mindestens zu berücksichtigen:

```text
Provider
Datenklassen
Secrets
Toolrechte
Least Privilege
Prompt Injection
Dokumente als Daten statt Anweisungen
Logging ohne Secrets
BYOK-Trennung
Provider-Protokollierung
Reproduzierbarkeit, soweit einschlägig
```

Eine KI darf keine fachliche, rechtliche oder datenschutzrechtliche Freigabe selbst erteilen.

---

# 4.11 Profil `HIGH_PROTECTION`

Bei hohem oder sehr hohem Schutzbedarf sind die weitergehenden Anforderungen des Frameworks und gegebenenfalls zusätzliche Risikoanalysen zu berücksichtigen.

Das Profil darf nicht allein durch LLM-Vermutung gesetzt werden.

Zulässige Quellen:

```text
Projektkonfiguration
vorhandene Schutzbedarfsfeststellung
HUMAN_CONFIRMED decision
verbindliche Policy-Angabe
```

Bei `UNKNOWN` ist:

```text
REVIEW_REQUIRED
```

zu verwenden.

---

# 4.12 Statusmodell für Framework-Anforderungen

Für jede Framework-Anforderung ist mindestens einer der folgenden Statuswerte zu verwenden:

```text
OPEN
APPLICABLE
NOT_APPLICABLE_WITH_REASON
IMPLEMENTED
VERIFIED
DEVIATION_PENDING
DEVIATION_APPROVED
BLOCKED
```

`NOT_APPLICABLE_WITH_REASON` benötigt zwingend eine Begründung.

`DEVIATION_APPROVED` benötigt eine dokumentierte zuständige Entscheidung.

Ein LLM darf eine Abweichung vorschlagen, aber nicht selbst genehmigen.

---

# 4.13 Quality-Gate-Semantik

Ein technischer Gate-Status darf erst nach der Policy-Evaluation erzeugt werden.

Grundregeln:

```text
MUSS + APPLICABLE + nicht umgesetzt
    → FAIL oder BLOCKED

MUSS + begründete und genehmigte Abweichung
    → PASS_WITH_DEVIATION bzw. dokumentierter zulässiger Zustand

BEDINGT + Auslöser nicht gegeben
    → NOT_APPLICABLE_WITH_REASON

BEDINGT + Auslöser gegeben + nicht umgesetzt
    → FAIL oder BLOCKED

SOLL + nicht umgesetzt
    → WARNING oder REVIEW_REQUIRED

UNKNOWN Anwendbarkeit
    → REVIEW_REQUIRED
```

Zusätzlich gilt entsprechend `docs/verbindlichkeit.md`:

```text
Offene Entscheidungen blockieren nur abhängige Arbeiten,
nicht automatisch alle unabhängigen Arbeitsschritte.
```

Der Workflow muss deshalb Dependency-Beziehungen zwischen Policy-Entscheidungen und Arbeitsschritten modellieren.

---

# 4.14 PolicyEvaluationResult

Mindestens folgendes Modell vorsehen:

```text
PolicyEvaluationResult

framework_repository
framework_commit
artifact
applicability_context
profiles
requirements[]
overall_status
blocking_requirements[]
review_required[]
approved_deviations[]
```

Je Requirement mindestens:

```text
requirement_id
source_path
source_commit
binding_level
trigger
applicable
applicability_reason
status
evidence
derived_checks
decision_reference
```

---

# 4.15 FrameworkPolicyProvider

Implementiere einen Provider:

```python
class FrameworkPolicyProvider(Protocol):
    def load_requirements(...) -> RequirementSet:
        ...

    def evaluate(
        self,
        context: ApplicabilityContext,
    ) -> PolicyEvaluationResult:
        ...
```

Die konkrete Implementierung liest:

```text
janpow77/verwaltung-app-framework
```

und erfasst den verwendeten Commit SHA.

Bei nicht erreichbarem Framework-Repository darf kein veralteter Regelstand still als aktuell ausgegeben werden.

Zulässige Statuswerte:

```text
POLICY_SOURCE_UNAVAILABLE
POLICY_SOURCE_STALE
POLICY_SOURCE_CURRENT
```

---

# 4.16 Caching und Offline-Verwendung

Für Offline- oder abgeschottete Entwicklungsumgebungen darf ein lokaler Snapshot der Framework-Anforderungen genutzt werden.

Voraussetzungen:

- Commit SHA gespeichert,
- Snapshot-Zeitpunkt gespeichert,
- Herkunft dokumentiert,
- Stale-Erkennung vorhanden.

Ein Snapshot ist Cache, nicht neue Source of Truth.

---

# 4.17 Policy-Evaluation im Consolidator

Vor der Empfehlung einer Konsolidierung muss geprüft werden, ob die geplante Änderung:

- Sicherheitsgrenzen entfernt,
- Berechtigungsprüfungen umgeht,
- Audit-Trails reduziert,
- Mandantentrennung verändert,
- Freigabe- oder Nachweislogik verändert,
- Secrets oder Providerzugänge betrifft.

Der Consolidator darf solche Eigenschaften nicht als bloße Code-Duplikate behandeln.

Bei relevanter Änderung:

```text
SECURITY_OR_POLICY_REVIEW_REQUIRED
```

---

# 4.18 Policy-Evaluation im App-Refactorer

Vor und nach einem Refactoring ist die Framework-Anwendbarkeit erneut auszuwerten.

Ein Refactoring darf insbesondere nicht still:

- serverseitige Autorisierung entfernen,
- Rollenprüfung in die UI verlagern,
- Mandantentrennung schwächen,
- Vier-Augen-Logik umgehen,
- Audit-Logs entfernen,
- Nachweis-/Versionsschutz reduzieren,
- Secret Handling verschlechtern,
- Input- oder Upload-Validierung entfernen.

Die technische Optimierung hat hinter Sicherheits- und Nachweisanforderungen zurückzustehen.

---

# 4.19 Policy-Evaluation im Deployer

Vor `READY_FOR_DEPLOYMENT` ist eine Deployment-spezifische Policy-Evaluation durchzuführen.

Mindestens prüfen:

```text
Betriebsziel
Schutzbedarf
Service User
Dateirechte
Secrets
Konfiguration
Logging
Backup / Restore
Netzwerkzugriffe
Proxy
Health Check
Abhängigkeiten
SBOM
Lieferkette
Updatefähigkeit
```

Produktiv- beziehungsweise Pilotpakete dürfen nicht allein aufgrund erfolgreicher Unit Tests freigegeben werden.

---

# 4.20 Integration mit dem Prüfkatalog

`docs/pruefkatalog.md` enthält Akzeptanzkriterien und keine Behauptung bereits bestandener Tests.

Der Policy Provider muss anwendbare Prüffälle ableiten.

Beispiele:

```text
Mehrmandantentrennung anwendbar
    → T-01

Rollen anwendbar
    → T-02

verbindliche Freigaben anwendbar
    → T-06

Uploads anwendbar
    → T-07

KI verarbeitet Dokumente
    → T-19

persönliche KI-Verbindung
    → T-25

auslieferbare Software
    → T-37

Architekturgrenzen
    → T-38
```

Nicht anwendbare Prüffälle dürfen nicht künstlich ausgeführt und als Fehler bewertet werden.

---

# 4.21 Security Baseline und BSI-Bezug

`docs/security/bsi-baseline.md` ist als projektbezogene Sicherheitsbaseline zu berücksichtigen.

Sie darf nicht als Behauptung einer:

- BSI-Zertifizierung,
- vollständigen Grundschutzprüfung,
- vollständigen Risikoanalyse

interpretiert werden.

Soweit das Framework für erhöhten Schutzbedarf weitergehende Bewertungen verlangt, sind diese als zusätzliche projektbezogene Anforderungen zu behandeln.

---

# 4.22 Lieferkette

Für auslieferbare Software sind die Vorgaben aus:

```text
docs/security/lieferkette.md
```

in die anwendbaren Quality- und Deployment-Gates einzubeziehen.

Insbesondere soll die Plattform technische Nachweise zu:

```text
Dependencies
Versionen
Artefakten
SBOM
Digests
Build
Tests
Nachtests
```

unterstützen.

---

# 4.23 Security-Anforderungen dürfen Optimierung begrenzen

Performance-, Architektur- oder Code-Optimierung darf nicht allein deshalb übernommen werden, weil sie:

- weniger Code,
- schnellere Laufzeit,
- weniger Datenbankzugriffe,
- weniger Logging

erzeugt.

Wenn dadurch eine anwendbare Sicherheits-, Nachweis- oder Governance-Anforderung geschwächt wird, ist die Optimierung abzulehnen oder anzupassen.

Es gilt:

```text
SECURITY AND AUDITABILITY
BEFORE MICRO-OPTIMIZATION
```

---

# 4.24 Framework Policy Gate im Gesamtworkflow

Der Gesamtworkflow wird erweitert zu:

```text
GitHub Repository
        ↓
ApplicabilityContext
        ↓
FrameworkPolicyProvider
        ↓
PolicyEvaluationResult
        ↓
Repository Inventory
        ↓
KIRA / Graphify
        ↓
Consolidation Plan
        ↓
Policy Impact Check
        ↓
auditcore / Shared Domain Module
        ↓
App Refactoring
        ↓
Policy Re-Evaluation
        ↓
Quality Gates + Applicable Framework Tests
        ↓
READY_FOR_DEPLOYMENT
        ↓
Deployment Policy Evaluation
        ↓
Package Build
        ↓
Install / Upgrade / Health Tests
```

---

# 4.25 Definition of Done für Policy-Integration

Die Framework-Integration ist erst fertig, wenn:

- `verwaltung-app-framework` als externe Source of Truth konfigurierbar ist,
- Commit SHA erfasst wird,
- `docs/verbindlichkeit.md` technisch berücksichtigt wird,
- MUSS/BEDINGT/SOLL unterschieden werden,
- Auslöser bewertet werden,
- Nichtanwendbarkeit begründet gespeichert wird,
- Security-Profile nur als abgeleitete Convenience-Schicht dienen,
- keine Profilregel die Framework-Quelle überschreibt,
- Prüffälle aus `docs/pruefkatalog.md` anwendbarkeitsabhängig abgeleitet werden,
- Abweichungen nicht durch ein LLM genehmigt werden können,
- offene Entscheidungen nur abhängige Schritte blockieren,
- Policy-Ergebnisse in KIRA gespeichert werden können,
- Refactoring und Deployment dieselben Policy-Ergebnisse berücksichtigen,
- Stale-Erkennung für Framework-Snapshots funktioniert.


# 5. Repository-Struktur

Zielstruktur:

```text
auditcore/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── AUDITCORE_LASTENHEFT.md
├── .gitignore
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       └── quality.yml
│
├── src/
│   └── auditcore/
│       ├── __init__.py
│       ├── exceptions.py
│       │
│       ├── models/
│       ├── rules/
│       ├── provenance/
│       ├── utils/
│       │
│       ├── risk/
│       ├── sampling/
│       ├── procurement/
│       ├── grants/
│       ├── documents/
│       ├── reporting/
│       ├── validation/
│       ├── anonymization/
│       │
│       └── tools/
│           ├── __init__.py
│           ├── quality/
│           │   ├── cli.py
│           │   ├── checks/
│           │   └── reporting/
│           │
│           ├── consolidator/
│           │   ├── cli.py
│           │   ├── workflow/
│           │   ├── providers/
│           │   ├── prompts/
│           │   ├── policies/
│           │   └── reporting/
│           │
│           ├── apprefactor/
│           │   ├── cli.py
│           │   ├── analysis/
│           │   ├── refactoring/
│           │   ├── migration/
│           │   ├── optimization/
│           │   └── verification/
│           │
│           └── deployer/
│               ├── cli.py
│               ├── discovery/
│               ├── build/
│               ├── debian/
│               ├── apt/
│               ├── validation/
│               └── reporting/
│
├── tests/
│   ├── core/
│   ├── quality/
│   ├── consolidator/
│   ├── apprefactor/
│   ├── deployer/
│   ├── regression/
│   ├── architecture/
│   └── security/
│
├── benchmarks/
├── examples/
└── docs/
```

Die Tools werden logisch getrennt, aber zunächst gemeinsam versioniert und ausgeliefert.

CLI-Einstiegspunkte:

```text
auditcore-quality
auditcore-consolidate
auditcore-refactor
auditcore-deploy
```

Installation zunächst:

```bash
pip install auditcore
```

bzw. für Entwicklung:

```bash
pip install -e ".[dev]"
```

Optionale schwere Abhängigkeiten sind über Extras zu kapseln, z. B.:

```text
auditcore[quality]
auditcore[analysis]
auditcore[deploy]
auditcore[all]
```

---

# 6. Komponente `auditcore`

## 6.1 Zweck

`auditcore` ist die zentrale, frameworkunabhängige Fachbibliothek.

Sie soll langfristig gemeinsame Fachlogik aus mehreren Anwendungen aufnehmen.

Beispiele möglicher Domains:

```text
auditcore/
    risk/
    sampling/
    procurement/
    grants/
    findings/
    documents/
    reporting/
    accounting/
    validation/
    anonymization/
```

Noch nicht vorhandene Fachregeln dürfen nicht erfunden werden.

## 6.2 Erlaubt

- reine Python-Funktionen
- Python-Klassen
- Dataclasses
- Enums / StrEnum
- Protocols
- TypedDict
- Pydantic-Modelle, wenn sinnvoll
- fachliche Exceptions
- RuleSets
- versionierte Konfigurationen

## 6.3 Nicht erlaubt im Kern

- FastAPI Router
- Flask
- Django Views
- SQLAlchemy Sessions
- konkrete Datenbankverbindungen
- konkrete HTTP-Clients
- Vue
- React
- UI-Logik
- Routing
- anwendungsspezifische Authentifizierung

---

# 7. Basis-Modelle in `auditcore`

Mindestens vorzusehen:

```text
CheckResult
CheckStatus
RuleSet
RuleSetMetadata
ValidationResult
SourceReference
ProvenanceRecord
```

Bevorzuge Standardbibliothek und kleine Runtime-Abhängigkeiten.

---

# 8. Provenienz in `auditcore`

Jede migrierte Funktion muss auf ihre Herkunft zurückgeführt werden können.

Beispiel:

```python
SourceReference(
    repository="flowaudit",
    path="src/services/risk.py",
    symbol="calculate_risk",
    revision="abc123"
)
```

Eine `auditcore`-Funktion darf mehrere Ursprungsquellen besitzen.

Zu speichern:

```text
source_repository
source_path
source_symbol
source_revision
migration_version
```

---

# 9. Versionierbare RuleSets

Veränderliche Regeln wie:

- Schwellenwerte
- Fristen
- Prozentsätze
- Rechtsstände
- Prüfkriterien

sollen möglichst nicht hart im Code verborgen werden.

Bevorzuge versionierbare RuleSets oder Konfigurationen.

Beispiel:

```text
auditcore/
    procurement/
        engine.py
        models.py
        rules/
            eu_2021_2027.yaml
            hesse_2026.yaml
```

Keine Rechtsregel darf erfunden werden.

---

# 10. Komponente `auditcore.tools.quality`

## 10.1 Zweck

`auditcore.tools.quality` ist ein ausführbares Quality Gate für `auditcore` und andere Python-Bibliotheken.

CLI:

```bash
auditcore-bibquality PATH
```

Mindestens:

```bash
auditcore-bibquality src/auditcore
auditcore-bibquality src/auditcore --format json
auditcore-bibquality src/auditcore --format text
auditcore-bibquality src/auditcore --strict
auditcore-bibquality src/auditcore --output report.json
auditcore-bibquality src/auditcore --no-external-tools
```

---

# 11. Maschinenlesbare Statuswerte

Zulässige Statuswerte:

```text
PASS
FAIL
WARNING
REVIEW_REQUIRED
NOT_EXECUTED
NOT_CONFIGURED
```

---

# 12. Quality-Codes

Mindestens:

```text
AC-SYN-001
AC-ARCH-001
AC-ARCH-002
AC-TYPE-001
AC-DOC-001
AC-SEC-001
AC-OSS-001
AC-DEP-001
AC-COMP-001
AC-API-001
AC-TEST-001
```

---

# 13. Syntaxprüfung

`AC-SYN-001`

Prüfung aller Python-Dateien über AST bzw. `compile`.

Syntaxfehler:

`FAIL`

---

# 14. Framework-Unabhängigkeit

`AC-ARCH-001`

Im Fachkern verboten:

```text
fastapi
flask
django
starlette
```

AST-basierte Prüfung, keine reine Textsuche.

---

# 15. Infrastruktur-Unabhängigkeit

`AC-ARCH-002`

Im Fachkern grundsätzlich nicht zulässig:

```text
sqlalchemy.orm.Session
psycopg
asyncpg
requests
httpx
konkrete DB-Verbindungen
Frontend-Abhängigkeiten
```

Konfigurierbar machen.

---

# 16. Datenschutz- und Open-Source-Prüfung

`AC-OSS-001`

Suche mindestens nach:

- IPv4
- IPv6
- `.local`
- `.internal`
- localhost
- UNC-Pfaden
- absoluten Windows-Pfaden
- absoluten Home-Pfaden
- internen URLs
- E-Mail-Adressen
- auffälligen Benutzernamen

Treffer standardmäßig:

`REVIEW_REQUIRED`

Nicht automatisch `FAIL`.

Ignore-Regeln unterstützen.

---

# 17. Secret Scanner

`AC-SEC-001`

Mindestens erkennen:

- API Keys
- Bearer Tokens
- Passwörter
- Access Tokens
- Private Keys
- JWT-ähnliche Tokens

Keine echten Secrets in Tests verwenden.

---

# 18. Dokumentationsprüfung

`AC-DOC-001`

Öffentliche:

- Funktionen
- Klassen
- Methoden

sollen Docstrings besitzen.

Für `auditcore` sollen öffentliche APIs möglichst deutsch und englisch dokumentiert sein.

Automatisch prüfbar:

- Docstring vorhanden
- Parameter dokumentiert
- Rückgabewerte dokumentiert
- Exceptions dokumentiert
- beide Sprachbereiche vorhanden

Semantische Qualität bleibt separate Prüfung.

---

# 19. Typprüfung

Unterstützen:

```text
mypy
```

optional:

```text
pyright
```

Nicht installiert:

`NOT_EXECUTED`

---

# 20. Ruff

Zentral in `pyproject.toml`.

Mindestens:

```text
E
F
I
UP
B
SIM
```

---

# 21. Security Tools

Optional integrieren:

```text
bandit
pip-audit
```

Nicht installiert:

`NOT_EXECUTED`

---

# 22. Komplexitätsprüfung

`AC-COMP-001`

Mindestens prüfen:

- sehr große Funktionen
- zu viele Parameter
- tiefe Verschachtelung
- hohe zyklomatische Komplexität

Standard:

`WARNING`

Grundsatz:

`AUDITABILITY OVER CLEVERNESS`

---

# 23. API-Stabilität

`AC-API-001`

Unterstützen:

```bash
auditcore-bibquality src/auditcore --api-snapshot api.json
auditcore-bibquality src/auditcore --compare-api api.json
```

Erfassen:

- öffentliche Module
- Klassen
- Funktionen
- Signaturen
- Rückgabetypen
- Exceptions, soweit technisch erfassbar

Breaking Changes kennzeichnen:

`BREAKING_CHANGE`

---

# 24. Regression und Golden Master

Infrastruktur vorsehen für:

```text
Legacy implementation
        ↓
Known Input
        ↓
Known Output
        ↓
Characterization Test
        ↓
auditcore implementation
        ↓
Comparison
```

Bei unerklärbarer Abweichung:

`MIGRATION_BLOCKED`

---

# 25. Konfiguration von `auditcore.tools.quality`

Konfiguration über `pyproject.toml`.

Beispiel:

```toml
[tool.auditcore-bibquality]
strict = false

forbidden-imports = [
    "fastapi",
    "flask",
    "django",
    "sqlalchemy.orm"
]

exclude = [
    "tests/fixtures/**"
]
```

CLI-Optionen haben Vorrang.

---

# 26. Ignore-Kommentare

Unterstützen:

```python
# auditcore-quality: ignore AC-OSS-001
```

oder dateiweit:

```python
# auditcore-quality: ignore-file AC-DOC-001
```

Keine globalen stillen Ausnahmen.

---

# 27. Exit Codes

```text
0 = PASS oder akzeptierte Warnungen
1 = FAIL
2 = ungültiger Aufruf oder technischer Fehler
```

---

# 28. Komponente `auditcore.tools.consolidator`

## 28.1 Zweck

Der Consolidator ist die zentrale Analyse- und Planungsinstanz für:

- Repository-Inventur
- GitHub-Analyse
- KIRA-Synchronisierung
- Graphify-Analyse
- Bibliothekskandidaten
- Konfliktanalyse
- Provenienz
- Characterization-Planung
- Konsolidierungsplanung
- Übergabe an `auditcore.tools.apprefactor`
- KIRA-Update

---

# 29. GitHub als Primärquelle

GitHub ist die primäre Wahrheit über den tatsächlichen Quellcode.

KIRA darf niemals GitHub ersetzen.

Es gilt:

```text
GITHUB = PRIMARY SOURCE OF CODE TRUTH
KIRA = SEMANTIC SEARCH AND KNOWLEDGE INDEX
GRAPHIFY = STRUCTURAL DEPENDENCY ANALYSIS
```

---

# 30. GitHub-Account-Inventur

Bei Erstinitialisierung alle relevanten Repositories des aktuell authentifizierten GitHub-Benutzers inventarisieren.

Unterscheiden:

```text
OWNED
ORGANIZATION
PRIVATE
PUBLIC
FORK
ARCHIVED
ACTIVE
```

Während der Inventur noch keinen Produktionscode verändern.

---

# 31. Betriebsmodi

Es gibt drei verbindliche Modi:

## GLOBAL

Für:

- Erstinventur
- Gesamtinventur
- Architekturprüfung
- Suche nach Duplikaten
- Suche nach Bibliothekskandidaten

## REPO

Nur aktuelles oder angegebenes Repository.

Für:

- lokale Bugs
- UI
- API
- anwendungsspezifische Änderungen
- lokale Refactorings

## REPO_AUDITCORE

Aktuelles Repository plus:

- `auditcore`
- bekannte Shared Libraries
- relevante KIRA-Fundstellen
- Graphify-Abhängigkeiten

Standardmodus für Fachlogik.

---

# 32. Automatische Moduswahl

Regeln:

```text
UI/API/lokale Infrastruktur
    → REPO

Fachlogik/Datenmodelle/Parser/Validierung/Berechnung
    → REPO_AUDITCORE

Gesamtanalyse/Bibliothekslandschaft
    → GLOBAL
```

Bei Unsicherheit über gemeinsame Fachlogik:

`REPO_AUDITCORE`

---

# 33. Erstinitialisierung

Wenn kein gültiger Repository-Katalog vorliegt:

`GLOBAL INITIAL INVENTORY`

muss automatisch durchgeführt werden.

Keine Konsolidierung vor Abschluss der Erstinventur.

---

# 34. Repository-Metadaten

Je Repository mindestens erfassen:

```text
Repositoryname
Owner
Visibility
Default Branch
Archived
Fork
Primary Language
weitere Sprachen
letzter relevanter Commit
Projektart
Package Manager
Python-Version
Frameworks
Tests vorhanden
CI vorhanden
Lizenz
```

Wichtige Dateien:

```text
pyproject.toml
requirements.txt
setup.py
setup.cfg
package.json
Dockerfile
docker-compose.yml
.github/workflows/*
README*
```

---

# 35. Zweistufige Inventur

## Phase 1: Metadata Inventory

Alle Repositories.

## Phase 2: Structural Code Inventory

Nur relevante aktive Code-Repositories.

Reine Dokumentations-, Build- oder unveränderte Fork-Repositories dürfen mit Begründung von Tiefenanalyse ausgeschlossen werden.

---

# 36. Codeinventar

Erfassen:

```text
Packages
Module
Klassen
Funktionen
Methoden
Enums
Dataclasses
Pydantic Models
Protocols
Konstanten
Rule Engines
Parser
Exporter
Importer
Validatoren
Berechnungslogik
Dokumentenlogik
Reportinglogik
Prüflogik
Risikologik
Stichprobenlogik
Vergabelogik
```

---

# 37. Symbolinventar

Für relevante Symbole mindestens:

```text
repository
path
module
symbol
symbol_type
signature
docstring_summary
imports
callers
callees
framework_dependencies
database_dependencies
domain_category
commit_sha
```

Wenn möglich:

```text
test_coverage
last_change
```

---

# 38. Persistentes Inventar

Lokale bzw. maschinenlesbare Speicherung:

```text
.auditcore/
    inventory/
        repositories.json
        symbols.json
        dependencies.json
        libraries.json
        consumers.json
        migrations.json
        inventory_metadata.json
```

Alternativ geeignete lokale Datenbank.

Metadaten:

```text
inventory_version
generated_at
repository_revision
scan_scope
scanner_version
```

---

# 39. Inkrementelle Inventur

Nach Erstinventur:

Vergleich anhand von:

```text
repository
branch
commit_sha
```

Unveränderte Repositories nicht vollständig neu analysieren.

---

# 40. KIRA RAG als persistenter Wissensspeicher

KIRA speichert nicht nur Embeddings von Code, sondern strukturiertes Wissen.

Mindestens folgende Dokumenttypen:

```text
REPOSITORY
SOURCE_FILE
SYMBOL
DEPENDENCY
DOMAIN_CONCEPT
LIBRARY_CANDIDATE
PROVENANCE
QUALITY_REPORT
CONSOLIDATION_REPORT
MIGRATION
ARCHITECTURE_DECISION
PROMPT
POLICY
```

---

# 41. KIRA-Datenmodell für Repositories

Mindestens:

```text
Repository-ID
Owner
Repositoryname
Visibility
Default Branch
Commit SHA
Projektart
Programmiersprachen
Frameworks
interne Packages
externe Dependencies
Tests
CI
Lizenz
Inventurdatum
```

---

# 42. KIRA-Datenmodell für Symbole

Mindestens:

```text
repository
commit_sha
path
module
symbol
symbol_type
signature
docstring
summary
domain
dependencies
callers
callees
framework_dependencies
database_dependencies
```

---

# 43. KIRA-Versionierung

Jeder repositorybezogene KIRA-Eintrag braucht:

```text
repository
branch
commit_sha
path
symbol
indexed_at
```

Wenn:

```text
KIRA commit_sha != aktueller GitHub commit_sha
```

dann:

`STALE`

---

# 44. Secret- und Datenschutzprüfung vor KIRA

Vor Indexierung mindestens prüfen:

- Passwörter
- API Keys
- Access Tokens
- Private Keys
- personenbezogene Testdaten
- interne IP-Adressen
- interne URLs
- interne Hostnamen
- absolute interne Pfade

Secrets dürfen nicht in KIRA gespeichert werden.

---

# 45. KIRA-Semantik

Nach struktureller GitHub-Inventur KIRA für semantische Ähnlichkeit nutzen.

Beispiel:

```text
calculate_risk
score_project
bewerte_vorhaben
ermittle_risikoklasse
```

können demselben Fachkonzept zugeordnet werden.

KIRA ergänzt GitHub.

KIRA ersetzt GitHub nicht.

---

# 46. KIRA-Wissensklassifikation

LLM-generierte Erkenntnisse dürfen nicht ungeprüft als Fakten gespeichert werden.

Jedes Wissenselement erhält eine Klassifikation:

```text
OBSERVED
DERIVED
LLM_INFERRED
HUMAN_CONFIRMED
```

Optional:

```text
confidence: 0.0 - 1.0
```

Confidence ersetzt keine fachliche Freigabe.

---

# 47. Graphify

Graphify analysiert:

```text
imports
callers
callees
dependency chains
shared helpers
framework coupling
database coupling
cross-repository dependencies
```

Neue Symbole aus Graphify müssen wieder in GitHub/KIRA geprüft werden können.

---

# 48. Iterative Dependency Expansion

Ablauf:

```text
GitHub
  ↓
Symbol
  ↓
KIRA
  ↓
ähnliche Symbole
  ↓
Graphify
  ↓
weitere Helper
  ↓
GitHub
  ↓
weitere Prüfung
```

Wiederholen, bis fachlich relevante Abhängigkeiten hinreichend vollständig sind.

---

# 49. Provider-Abstraktionen

Mindestens:

```python
class RepositoryProvider(Protocol):
    ...

class InventoryProvider(Protocol):
    ...

class DependencyGraphProvider(Protocol):
    ...

class KnowledgeStore(Protocol):
    ...

class SemanticAnalysisProvider(Protocol):
    ...
```

KIRA und Graphify nicht fest in den Domain Core koppeln.

---

# 50. KIRA-Adapter

Semantisch mindestens folgende Frage unterstützen:

> Welche Bibliotheken, Module, Klassen und Funktionen existieren zu diesem fachlichen Konzept bereits in den verfügbaren Repositories?

Kein Treffer:

`NOT_FOUND_IN_CURRENT_INDEX`

nicht:

`DOES_NOT_EXIST`

---

# 51. Graphify-Adapter

Mindestens:

- Imports
- Aufrufer
- Aufgerufene Funktionen
- Klassenabhängigkeiten
- Frameworkkopplung
- Datenbankkopplung
- gemeinsame Helper

---

# 52. Bibliothekskandidaten

Nach GLOBAL-Inventur Kandidaten erkennen.

Beispiele:

```text
Dokumentenverarbeitung
Risikobewertung
Stichproben
Berichterstellung
Prüfstatus
Validierung
Vergabeprüfung
Datenanalyse
Anonymisierung
Office-Verarbeitung
```

---

# 53. Bewertung eines Kandidaten

Dokumentieren:

```text
betroffene Repositories
betroffene Symbole
Anzahl ähnlicher Implementierungen
fachliche Gemeinsamkeit
technische Gemeinsamkeit
Frameworkkopplung
Datenbankkopplung
bekannte Tests
Consumer
Konflikte
vorgeschlagenes Zielmodul
```

---

# 54. Bibliotheksvorschläge

Primär:

`auditcore`

Mögliche weitere Bibliotheken:

```text
auditcore-documents
auditcore-office
auditcore-reporting
auditcore-data
auditcore-ml
```

Neue Bibliothek nur mit dokumentierter Begründung.

Keine unnötigen Micro-Packages.

---


---

# 54A. Policy gegen unnötige Paketfragmentierung

Neue gemeinsam nutzbare Fachlogik soll standardmäßig als Domain-Modul innerhalb von `auditcore` angelegt werden.

Beispiele:

```text
auditcore.documents
auditcore.office
auditcore.reporting
auditcore.risk
auditcore.sampling
auditcore.procurement
```

Nicht automatisch:

```text
auditcore-documents
auditcore-office
auditcore-reporting
auditcore-data
auditcore-ml
```

Ein eigenständiges zusätzliches Python-Paket darf nur vorgeschlagen werden, wenn mindestens einer der folgenden Gründe nachvollziehbar vorliegt:

- eigenständiger Releasezyklus ist erforderlich,
- große oder spezielle Runtime-Abhängigkeiten würden den Core unnötig belasten,
- das Paket ist unabhängig von `auditcore` sinnvoll nutzbar,
- inkompatible Plattformanforderungen bestehen,
- klare organisatorische oder technische Eigentumsgrenzen bestehen.

Es gilt:

```text
DEFAULT = MODULE INSIDE AUDITCORE
SEPARATE PACKAGE = EXCEPTION REQUIRING JUSTIFICATION
```

Dadurch soll eine unnötige Micro-Package-Landschaft vermieden werden.


# 55. Library Candidate Report

Beispiel:

```text
LIBRARY CANDIDATE

Name:
auditcore.documents

Sources:
FlowAudit
LAMA
Audit-Designer

Functions detected:
12

Semantic duplicates:
7

Framework coupling:
low

Expected reuse:
high

Recommendation:
EXTRACT
```

---

# 56. Konfliktanalyse

Statuswerte:

```text
IDENTICAL
TECHNICALLY_DIFFERENT
SEMANTICALLY_EQUIVALENT
SEMANTICALLY_DIFFERENT
POLICY_DIFFERENCE
LEGAL_INTERPRETATION_DIFFERENCE
UNKNOWN
```

---

# 57. Human Decision Gate

Folgende Fälle dürfen nicht automatisch harmonisiert werden:

- Rechtsauslegung
- Prüfmethodik
- Risikogewichtung
- Schwellenwerte
- Finanzkorrekturen
- widersprüchliche Fachregeln

Status:

`HUMAN_DECISION_REQUIRED`

---

# 58. Policies

Maschinenlesbare Policies:

```text
src/auditcore.tools.consolidator/policies/
    consolidation.yaml
    architecture.yaml
    human_decisions.yaml
    quality.yaml
```

Beispiel:

```yaml
policy_version: "1.0"

human_decision_required:
  - legal_interpretation
  - audit_methodology
  - risk_weighting
  - correction_rate
  - conflicting_business_rules

automatic_changes_allowed:
  - internal_refactoring
  - typing_improvement
  - documentation_improvement
  - dependency_decoupling
  - duplicate_technical_helper_consolidation
```

Workflow muss Policies tatsächlich lesen und verwenden.

---

# 59. Prompt-Bibliothek

Prompts versioniert speichern:

```text
src/auditcore.tools.consolidator/prompts/
    system.md
    global_inventory.md
    repo_analysis.md
    repo_auditcore.md
    library_detection.md
    conflict_analysis.md
    consolidation.md
    migration.md
    optimization.md
```

Prompts auch nach Installation zugänglich machen, vorzugsweise über `importlib.resources`.

---

# 60. Prompt-Versionierung

Jeder Prompt braucht Metadaten, z. B.:

```yaml
name: consolidation
version: "1.0"
```

Verwendete Promptversionen in Berichten speichern.

---

# 61. Trennung Prompt / Policy / Workflow

Prompt:

```text
Wie analysiert das LLM?
```

Policy:

```text
Was darf entschieden werden?
```

Workflow-Code:

```text
Welche Schritte müssen ausgeführt werden?
```

Diese drei Ebenen nicht vermischen.

---

# 62. Characterization Tests

Vor Migration bestehender Fachlogik Verhalten dokumentieren.

Modelle:

```text
CharacterizationCase
LegacyResult
AuditCoreResult
RegressionComparison
```

Schema:

```text
Legacy Code
   ↓
Known Input
   ↓
Known Output
   ↓
Characterization Test
```

---

# 63. Consolidation Plan

Strukturiertes Modell:

```text
ConsolidationPlan

target_module
target_symbols
sources
technical_dependencies
domain_dependencies
conflicts
human_decisions
tests_required
migration_strategy
```

Vor Implementierung erzeugen.

---

# 64. Konsolidierung

Nach erfolgreicher Analyse:

1. Zielmodul festlegen
2. API definieren
3. Provenienz speichern
4. Characterization Tests übernehmen
5. Fachlogik von Infrastruktur trennen
6. Implementierung erzeugen
7. Unit Tests erzeugen
8. `auditcore.tools.quality` ausführen

---

# 65. Fachanwendungen migrieren

Aufgabe endet nicht mit Bibliothekserstellung.

Betroffene Anwendungen anschließend migrieren.

Beispiel:

```python
from app.services.risk import calculate_risk
```

wird:

```python
from auditcore.risk import calculate_risk
```

---

# 66. Schrittweise Migration

Bevorzuge:

```text
Legacy Function
      ↓
Compatibility Wrapper
      ↓
auditcore
      ↓
Consumer Migration
      ↓
Tests
      ↓
Deprecation
```

Keine unkontrollierte Big-Bang-Migration.

---

# 67. Consumer Registry

KIRA und lokales Inventar speichern:

```text
auditcore.documents.extract_tables

Consumers:
- FlowAudit
- Audit-Designer
- eCohesion
```

---

# 68. Impact Analysis

Vor Änderungen gemeinsamer APIs prüfen:

```text
Welche Consumer sind betroffen?
Welche Tests müssen ausgeführt werden?
Welche Breaking Changes entstehen?
```

---

# 69. API-Brüche

Erkennen:

```text
renamed functions
removed functions
changed parameters
changed return types
changed exceptions
changed models
```

Kennzeichnen:

`BREAKING_CHANGE`

---

# 70. Tests nach Migration

Mindestens:

```text
auditcore tests
+
betroffene application tests
+
integration tests
```

Vorhandene Tools verwenden:

```text
pytest
npm test
vitest
playwright
ruff
mypy
```

Keine erfundenen Ergebnisse.

---

# 71. Optimization Phase

Erst nach fachlicher Gleichheit.

Prüfen:

```text
Code duplication
API design
Typing
Performance
Memory
Complexity
Dependencies
Testability
```

Danach erneut:

```text
Regression Tests
+
BibQuality
+
Application Integration Tests
```

---

# 72. auditcore.tools.quality Reports in KIRA

Speichern:

```text
QUALITY_REPORT

library
version
commit
quality_status
tests
coverage
findings
checked_at
```

KIRA soll geprüfte und ungeprüfte Implementierungen unterscheiden können.

---

# 73. Migrationen in KIRA

Beispiel:

```text
MIGRATION

Source:
FlowAudit.documents.extract_tables

Target:
auditcore.documents.extract_tables

Status:
COMPLETE

Source Commit:
...

Target Commit:
...

Regression:
PASS
```

---

# 74. Architekturentscheidungen in KIRA

Beispiel:

```text
ARCHITECTURE_DECISION

Decision:
Document parsing belongs to auditcore.documents

Reason:
Used by several applications and independent from application infrastructure.

Related symbols:
...
```

---

# 75. KIRA-Update nach jeder Änderung

Nach erfolgreicher Konsolidierung mindestens aktualisieren:

```text
neue Symbole
geänderte Symbole
Dependencies
Consumer
Provenienz
Quality Status
Migration
API Snapshot
Architecture Decisions
```

---

# 76. Workflow-State-Machine

Mindestens:

```text
CREATED

INVENTORY_REQUIRED
INVENTORY_RUNNING
INVENTORY_COMPLETE

KIRA_SYNCHRONIZED

CANDIDATES_DETECTED
DEPENDENCIES_ANALYZED
CONFLICTS_ANALYZED

WAITING_FOR_HUMAN_DECISION

READY_FOR_CONSOLIDATION
CHARACTERIZED

LIBRARY_CREATED
LIBRARY_TESTED

APPLICATIONS_MIGRATED
APPLICATIONS_TESTED

QUALITY_CHECKED
OPTIMIZED
KIRA_UPDATED

COMPLETE
FAILED
```

Ungültige Übergänge verhindern.

---

# 77. Abschlussbedingung einer Migration

`COMPLETE` erst wenn:

- Library erstellt
- Unit Tests bestanden
- Regression Tests bestanden
- Quality Gate bestanden
- Consumer angepasst
- Consumer getestet
- Integration getestet
- Provenienz gespeichert
- KIRA aktualisiert

---

# 78. CLI von `auditcore.tools.consolidator`

Mindestens:

```bash
auditcore-consolidate inventory --global
auditcore-consolidate inventory --update
auditcore-consolidate libraries
auditcore-consolidate analyse REPOSITORY
auditcore-consolidate analyse REPOSITORY --with-auditcore
auditcore-consolidate migrate SYMBOL
auditcore-consolidate status
auditcore-consolidate kira sync
```

---

# 79. Dry Run

Unterstützen:

```bash
auditcore-consolidate migrate \
    FlowAudit:calculate_risk \
    --dry-run
```

Dry Run darf keine Repositorydateien verändern.

---

# 80. Programmatic API

Beispiel:

```python
inventory = GlobalInventory(...)
result = inventory.scan_authenticated_account()
```

und:

```python
workflow = ConsolidationWorkflow(...)

result = workflow.run(
    repository="flowaudit",
    mode=WorkflowMode.REPO_AUDITCORE,
)
```

---

# 81. Berichte

Mindestens:

```text
Markdown
JSON
```

Optional:

```text
HTML
```

---

# 82. Gesamtinventur-Bericht

Nach Erstinventur:

## Repositorylandschaft

- Anzahl Repositories
- aktiv
- archiviert
- private
- public
- forks

## Technologielandschaft

- Sprachen
- Python-Versionen
- Frameworks
- Package Manager
- CI

## Interne Bibliotheken

- vorhandene Packages
- gemeinsame Helper
- Shared Modules

## Duplikate

- technische Duplikate
- semantische Duplikate

## Library Candidates

- mögliche auditcore-Module
- mögliche weitere Shared Libraries

## Consumer

- bekannte Anwendungen

## Risiken

- Konflikte
- starke Frameworkkopplung
- fehlende Tests
- veraltete Module

---

# 83. Bibliotheksroadmap

Sachlich-technische Roadmap.

Beispiel:

```text
Candidate:
Document parsing

Repositories:
4

Implementations:
6

Commonality:
high

Framework coupling:
low

Suggested target:
auditcore.documents

Migration complexity:
medium
```

Keine verdeckte fachliche Entscheidung.

---

# 84. Reuse Gate vor neuem Code

Vor neuer Fachlogik prüfen:

```text
Existiert lokal bereits etwas?

Existiert es in auditcore?

Existiert es in Shared Libraries?

Kennt das Inventar ähnliche Implementierungen?

Findet KIRA semantische Kandidaten?

Gibt es Graphify-Abhängigkeiten?
```

Erst dann neuen Code schreiben.

---

# 85. REPO_AUDITCORE Workflow

```text
Current Repository
        ↓
Current Inventory
        ↓
auditcore
        ↓
Known Shared Libraries
        ↓
KIRA
        ↓
Graphify
        ↓
Reuse / Extend / Consolidate / New Local Code
        ↓
Tests
        ↓
BibQuality
        ↓
Inventory Update
        ↓
KIRA Update
```

---

# 86. GLOBAL Workflow

```text
GitHub Account
      ↓
All Relevant Repositories
      ↓
Metadata Inventory
      ↓
Structural Inventory
      ↓
Symbol Inventory
      ↓
KIRA Sync
      ↓
Semantic Similarity
      ↓
Graphify Analysis
      ↓
Library Candidate Detection
      ↓
Architecture Report
      ↓
Migration Roadmap
```

---

# 87. REPO Workflow

```text
Repository
    ↓
Local Analysis
    ↓
Local Tests
    ↓
Change
    ↓
Tests
```

Wenn Fachlogik mit Shared-Core-Bezug erkannt:

Wechsel zu:

`REPO_AUDITCORE`

---

# 88. Teststrategie für den Consolidator

Mindestens Tests für:

- GitHub-Inventur
- Symbolanalyse
- inkrementelle Inventur
- KIRA-Synchronisierung
- Stale-Erkennung
- Provider-Abstraktionen
- Graphify-Integration
- Library Candidate Detection
- Conflict Detection
- Human Decision Gate
- State Machine
- Provenienz
- Consumer Registry
- Quality Report Speicherung
- Migration Status
- CLI
- JSON Reports
- Prompt Loading
- Policy Loading
- Prompt Versioning

---

# 89. Fake Provider

Tests dürfen keine echten externen Systeme benötigen.

Fake-/Mock-Provider für:

```text
GitHub
KIRA
Graphify
LLM
```

---

# 90. Logging

Logs dürfen keine:

- Tokens
- Secrets
- personenbezogenen Daten

enthalten.

---

# 91. Credentials

Keine Zugangsdaten im Repository.

Nur:

- Environment Variables
- Secret Stores
- Credential Provider

---

# 92. Run-ID

Jeder Workflow-Lauf erhält eindeutige Run-ID.

Mindestens speichern:

```text
run_id
started_at
mode
repositories
input_commit
output_commit
prompt_versions
policy_versions
tool_versions
result
```

---

# 93. Nichtfunktionale Anforderungen

Das System muss:

- modular
- testbar
- nachvollziehbar
- fehlertolerant
- erweiterbar
- frameworkunabhängig
- Open-Source-fähig
- inkrementell
- reproduzierbar

sein.

---

# 94. CI

GitHub Actions Workflow:

```text
.github/workflows/quality.yml
```

Mindestens:

- Python 3.11
- Python 3.12
- Python 3.13, soweit kompatibel

Ausführen:

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src
auditcore-bibquality src/auditcore --strict
auditcore-bibquality src/auditcore.tools.quality
auditcore-bibquality src/auditcore.tools.consolidator
```

Optional:

```bash
bandit
pip-audit
```

---

# 95. Packaging

Muss funktionieren:

```bash
pip install -e .
pip install .
```

CLI danach:

```bash
auditcore-bibquality --help
auditcore-consolidate --help
```

---

# 96. Runtime Dependencies

Möglichst klein halten.

Entwicklertools unter:

```toml
[project.optional-dependencies]
dev = [...]
quality = [...]
```

---

# 97. Dokumentation

README mindestens:

1. Zweck
2. Architektur
3. Installation
4. auditcore
5. bibquality
6. consolidator
7. GitHub-Inventur
8. KIRA
9. Graphify
10. Betriebsmodi
11. Quality Gates
12. Regressionstests
13. Prompt Library
14. Policies
15. Release-Prozess
16. Beitrag zur Entwicklung

---

# 98. Abnahmekriterien Phase 1

Erfolgreich, wenn:

1. alle relevanten GitHub-Repositories ermittelt werden,
2. Repository-Metadaten erfasst werden,
3. Python-Code strukturell inventarisiert wird,
4. Symbole katalogisiert werden,
5. Ergebnisse persistent gespeichert werden,
6. KIRA synchronisiert werden kann,
7. Commitstände mit KIRA verknüpft sind,
8. inkrementelle Aktualisierung funktioniert.

---

# 99. Abnahmekriterien Phase 2

Erfolgreich, wenn:

1. semantisch ähnliche Implementierungen erkannt werden,
2. Graphify-Abhängigkeiten analysiert werden,
3. Bibliothekskandidaten erkannt werden,
4. Provenienz dokumentiert wird,
5. Konflikte erkannt werden,
6. Human Decision Gates funktionieren.

---

# 100. Abnahmekriterien Phase 3

Erfolgreich, wenn:

1. eine reale Funktion aus einer Fachanwendung nach `auditcore` migriert werden kann,
2. Characterization Tests existieren,
3. Regression Tests bestehen,
4. `auditcore.tools.quality` erfolgreich läuft,
5. mindestens eine Fachanwendung migriert wurde,
6. Integrationstests bestehen,
7. Migration und Provenienz in KIRA gespeichert werden.

---

# 101. Abnahmekriterien Phase 4

Erfolgreich, wenn:

1. mehrere Consumer erkannt werden,
2. API-Impact-Analyse funktioniert,
3. Shared Libraries inkrementell weiterentwickelt werden,
4. KIRA Migrations- und Qualitätsstatus korrekt wiedergibt.

---

# 102. Definition of Done – Gesamtplattform

Die Aufgabe ist erst abgeschlossen, wenn:

- das Python-Projekt `auditcore` installierbar ist
- die Fachbibliothek `auditcore` importierbar ist
- die vier Tool-Komponenten `quality`, `consolidator`, `apprefactor` und `deployer` innerhalb desselben Projekts funktionsfähig sind
- alle CLIs funktionieren
- `auditcore-refactor --help` funktioniert
- `auditcore-deploy --help` funktioniert
- Prompt Library enthalten ist
- Policy Library enthalten ist
- State Machine funktioniert
- GitHub Provider funktioniert oder sauber `NOT_CONFIGURED` meldet
- KIRA Provider funktioniert oder sauber `NOT_CONFIGURED` meldet
- Graphify Provider funktioniert oder sauber `NOT_CONFIGURED` meldet
- Inventar persistiert werden kann
- KIRA Sync implementiert ist
- FrameworkPolicyProvider implementiert ist
- Policy-Evaluation nach `docs/verbindlichkeit.md` funktioniert
- anwendbare Prüffälle aus `docs/pruefkatalog.md` abgeleitet werden können
- Stale-Erkennung funktioniert
- Bibliothekskandidaten erkannt werden können
- Conflict Detection funktioniert
- Human Decision Gate funktioniert
- Provenienz gespeichert werden kann
- Characterization-Infrastruktur existiert
- ConsolidationPlan existiert
- Migrationen dokumentiert werden
- Consumer Registry existiert
- API Snapshot funktioniert
- Quality Reports funktionieren
- JSON Reports funktionieren
- Tests bestanden sind
- CI vorhanden ist
- Dokumentation vorhanden ist


---



# 100A. Vierte Kernkomponente: `auditcore.tools.apprefactor`

## 100A.1 Zweck

`auditcore.tools.apprefactor` ist eine eigenständige Python-Bibliothek und CLI für die kontrollierte technische Überarbeitung bestehender Fachanwendungen.

Sie übernimmt die konkrete Umsetzung der vom `auditcore.tools.consolidator` ermittelten Konsolidierungs- und Migrationspläne.

Der `auditcore.tools.consolidator` entscheidet also nicht selbst über die konkrete Anwendungstransformation.

Stattdessen gilt:

```text
auditcore.tools.consolidator
    Analyse + Konsolidierungsplan
        ↓
auditcore.tools.apprefactor
    konkrete Refactorings + Migration + Optimierung
        ↓
auditcore.tools.quality / Application Tests
        ↓
READY_FOR_DEPLOYMENT
        ↓
auditcore.tools.deployer
```

---

## 100A.2 Verantwortungsbereich

`auditcore.tools.apprefactor` übernimmt insbesondere:

- Ersetzen duplizierter Fachlogik durch Shared-Library-Aufrufe
- Migration auf `auditcore`
- Migration auf weitere gemeinsame Bibliotheken
- Erzeugen von Compatibility Wrappers
- Entfernen nicht mehr benötigter Legacy-Implementierungen nach erfolgreicher Migration
- Entkopplung von Framework- und Datenbanklogik
- Verbesserung der Modulstruktur
- Bereinigung von Imports
- Verbesserung von Type Hints
- Vereinheitlichung von Fehlerbehandlung
- Reduktion unnötiger Dependencies
- Verbesserung der Testbarkeit
- Performance-Optimierung
- Speicheroptimierung
- Verbesserung von Konfiguration und Dependency Injection
- API- und Service-Layer-Bereinigung
- technische Dokumentation der Anwendung

---

## 100A.3 Abgrenzung zum Consolidator

`auditcore.tools.consolidator`:

```text
DISCOVER
COMPARE
CLASSIFY
PLAN
```

`auditcore.tools.apprefactor`:

```text
CHANGE
MIGRATE
REFACTOR
OPTIMIZE
VERIFY
```

Der Consolidator soll möglichst wenig direkten Anwendungscode verändern.

Er erzeugt stattdessen strukturierte Pläne, die `auditcore.tools.apprefactor` verarbeitet.

---

## 100A.4 Zielstruktur

Mindestens:

```text
src/auditcore.tools.apprefactor/
├── __init__.py
├── cli.py
├── config.py
├── models/
│   ├── plan.py
│   ├── change.py
│   ├── migration.py
│   ├── optimization.py
│   └── verification.py
│
├── analysis/
│   ├── application_structure.py
│   ├── imports.py
│   ├── dependencies.py
│   ├── framework_coupling.py
│   └── database_coupling.py
│
├── refactoring/
│   ├── imports.py
│   ├── functions.py
│   ├── modules.py
│   ├── wrappers.py
│   ├── services.py
│   └── dependencies.py
│
├── migration/
│   ├── auditcore.py
│   ├── shared_libraries.py
│   ├── compatibility.py
│   └── cleanup.py
│
├── optimization/
│   ├── typing.py
│   ├── complexity.py
│   ├── performance.py
│   ├── memory.py
│   ├── testability.py
│   └── dependency_reduction.py
│
├── verification/
│   ├── regression.py
│   ├── integration.py
│   ├── application_tests.py
│   └── quality.py
│
├── providers/
│   ├── protocols.py
│   ├── git.py
│   └── kira.py
│
└── reporting/
```

---

## 100A.5 Eingabe

Primäre Eingabe ist ein strukturierter `ConsolidationPlan` aus `auditcore.tools.consolidator`.

Mindestens:

```text
target_application
source_commit
shared_library_target
symbols_to_replace
legacy_symbols
compatibility_strategy
characterization_tests
required_application_tests
known_consumers
known_conflicts
approved_human_decisions
```

---

## 100A.6 RefactoringPlan

Vor jeder Änderung erzeugt `auditcore.tools.apprefactor` einen eigenen `ApplicationRefactoringPlan`.

Mindestens:

```text
application
source_commit
target_shared_libraries
files_to_change
imports_to_change
symbols_to_replace
wrappers_to_create
tests_to_update
dependencies_to_remove
dependencies_to_add
optimization_steps
risk_level
rollback_strategy
```

---

## 100A.7 Dry Run

Vor tatsächlichen Änderungen muss ein Dry Run möglich sein.

Beispiel:

```bash
auditcore-refactor apply plan.json --dry-run
```

Der Dry Run zeigt:

- Dateien, die geändert würden
- Imports, die ersetzt würden
- Funktionen, die migriert würden
- Dependencies, die entfallen
- Tests, die betroffen sind
- mögliche API-Brüche

Keine Dateien verändern.

---

## 100A.8 CLI

Mindestens:

```bash
auditcore-refactor inspect REPOSITORY
auditcore-refactor plan REPOSITORY
auditcore-refactor apply PLAN
auditcore-refactor optimize REPOSITORY
auditcore-refactor verify REPOSITORY
auditcore-refactor status
```

Zusätzlich:

```bash
auditcore-refactor apply PLAN --dry-run
auditcore-refactor apply PLAN --format json
auditcore-refactor optimize REPOSITORY --safe
```

---

## 100A.9 Programmatic API

Beispiel:

```python
from auditcore.tools.apprefactor import ApplicationRefactorer

refactorer = ApplicationRefactorer(...)
result = refactorer.apply(plan)
```

---

## 100A.10 Migration auf `auditcore`

Beispiel:

Vorher:

```python
from app.services.risk import calculate_risk
```

Nachher:

```python
from auditcore.risk import calculate_risk
```

Wenn mehrere Consumer bestehen, erfolgt Migration kontrolliert je Anwendung.

---

## 100A.11 Compatibility Wrapper

Wenn ein sofortiger API-Wechsel nicht sinnvoll ist:

```python
from auditcore.risk import calculate_risk as _calculate_risk

def calculate_risk(*args, **kwargs):
    """Deprecated compatibility wrapper."""
    return _calculate_risk(*args, **kwargs)
```

Wrapper sollen:

- als deprecated markiert,
- getestet,
- später entfernbar

sein.

---

## 100A.12 Legacy Cleanup

Alter Code darf erst entfernt werden, wenn:

- Characterization Tests vorhanden sind,
- neue Shared-Library-Funktion getestet ist,
- Anwendung migriert wurde,
- Anwendungstests bestanden haben,
- Integrationsprüfung erfolgreich war,
- kein aktiver Consumer mehr auf Legacy-Code zugreift.

---

## 100A.13 Anwendungsoptimierung

Nach funktionaler Migration darf technische Optimierung erfolgen.

Prüfen:

```text
Modulstruktur
Importstruktur
Dependency Direction
Frameworkkopplung
DB-Kopplung
Type Hints
Fehlerbehandlung
Komplexität
Duplikate
Testbarkeit
Performance
Speicherverbrauch
Konfiguration
Logging
```

---

## 100A.14 Safe Optimization

Standardmodus:

```text
SAFE
```

Im SAFE-Modus dürfen nur Änderungen durchgeführt werden, bei denen die fachliche Semantik erhalten bleibt.

Beispiele:

- Extract Function
- Rename Internal Symbol
- Import Cleanup
- Type Improvements
- Dependency Injection
- Wrapper
- technische Duplikatbereinigung

Fachliche Regeländerungen sind nicht zulässig.

---

## 100A.15 Performance-Optimierung

Performanceoptimierungen nur:

- nach erfolgreicher Regression,
- mit Benchmark oder plausibler technischer Begründung,
- ohne fachliche Bedeutungsänderung.

Vergleich:

```text
BEFORE
AFTER
```

Mindestens bei performancekritischen Änderungen:

- Laufzeit
- Speicher
- Ergebnisgleichheit

---

## 100A.16 Dependency Reduction

Das Tool soll erkennen:

- nicht mehr verwendete Python-Pakete
- obsolete Frontend-Abhängigkeiten
- redundante Libraries
- Framework-Abhängigkeiten, die durch Shared Libraries entfallen

Entfernung erst nach Test.

---

## 100A.17 Framework-Entkopplung

Fachlogik soll aus:

- FastAPI Routes
- Django Views
- Flask Handlers
- SQLAlchemy Session-gebundener Logik

herausgelöst und durch Shared-Library-Aufrufe ersetzt werden.

Beispiel:

```text
HTTP Layer
    ↓
Application Service
    ↓
auditcore
```

---

## 100A.18 Datenbank-Entkopplung

Fachlogik soll möglichst nicht unmittelbar von konkreten Datenbank-Sessions abhängen.

Bevorzuge:

- Repository Interfaces
- Protocols
- DTOs
- Domain Models
- Dependency Injection

---

## 100A.19 Application Quality Gate

Nach Refactoring mindestens:

```text
Application Unit Tests
Regression Tests
Integration Tests
Ruff
Type Checking
Security Checks
Dependency Checks
auditcore.tools.quality für Shared Libraries
application-specific checks
```

---

## 100A.20 Refactoring Statuswerte

Mindestens:

```text
PLANNED
DRY_RUN_COMPLETE
APPLIED
TESTED
OPTIMIZED
VERIFIED
READY_FOR_DEPLOYMENT
BLOCKED
FAILED
```

---

## 100A.21 Eigene State Machine

```text
CREATED
APPLICATION_ANALYZED
REFACTOR_PLAN_CREATED
DRY_RUN_COMPLETE
LEGACY_CHARACTERIZED
MIGRATION_APPLIED
APPLICATION_TESTED
OPTIMIZATION_APPLIED
REGRESSION_VERIFIED
INTEGRATION_VERIFIED
QUALITY_VERIFIED
READY_FOR_DEPLOYMENT
FAILED
```

---

## 100A.22 Rückgabe an KIRA

Nach erfolgreicher Refactoring-Phase speichern:

```text
APPLICATION_REFACTOR
APPLICATION_OPTIMIZATION
APPLICATION_MIGRATION
```

Mindestens:

```text
application
source_commit
target_commit
shared_libraries
changed_symbols
removed_legacy_symbols
test_status
quality_status
optimization_summary
```

---

## 100A.23 Handoff an `auditcore.tools.deployer`

Nur wenn Status:

`READY_FOR_DEPLOYMENT`

darf ein Deployment-Handoff erzeugt werden.

Beispiel:

```json
{
  "application": "regulierung",
  "status": "READY_FOR_DEPLOYMENT",
  "git_commit": "...",
  "shared_libraries": {
    "auditcore": "0.4.0"
  },
  "tests": "PASS",
  "quality": "PASS"
}
```

---

## 100A.24 Tests des App-Refactorers

Mindestens Tests für:

- Plan Loading
- Dry Run
- Import Replacement
- Symbol Replacement
- Compatibility Wrapper
- Legacy Cleanup
- Dependency Removal
- Type Improvements
- Framework Decoupling
- Regression Verification
- Integration Verification
- State Machine
- JSON Reporting
- KIRA Handoff
- Deployer Handoff

---

## 100A.25 Leitprinzip

```text
CONSOLIDATOR DECIDES WHAT SHOULD CHANGE.

APPREFACTOR CHANGES THE APPLICATION.

BIBQUALITY CHECKS THE RESULT.

DEPLOYER SHIPS THE RESULT.
```


# 101A. Fünfte Kernkomponente: `auditcore.tools.deployer`

## 101A.1 Zweck

`auditcore.tools.deployer` ist eine eigenständige Python-Bibliothek und CLI für die reproduzierbare Paketierung und Bereitstellung vollständiger Fachanwendungen.

Sie darf nicht Bestandteil von `auditcore` und nicht bloß ein Hilfsmodul des `auditcore.tools.consolidator` sein.

Der `auditcore.tools.apprefactor` endet bei einer refaktorierten, migrierten, optimierten und getesteten Anwendung.

Der Deployer übernimmt anschließend:

```text
Fertige Anwendung
      ↓
Deployment-Analyse
      ↓
Build-Manifest
      ↓
Runtime-Auflösung
      ↓
Frontend-Build
      ↓
Backend-Paketierung
      ↓
Debian Packaging
      ↓
.deb
      ↓
Installationsprüfung
      ↓
Upgrade-Prüfung
      ↓
APT Repository / Dateiübertragung
      ↓
Zielserver
```

---

## 101A.2 Abgrenzung zum Consolidator

`auditcore.tools.consolidator` analysiert Repositories, erkennt wiederverwendbare Logik und erzeugt Konsolidierungspläne.

`auditcore.tools.apprefactor` übernimmt anschließend die konkrete Migration, das Refactoring und die Optimierung der Fachanwendungen.

`auditcore.tools.deployer` übernimmt ausschließlich den Release- und Deployment-Lebenszyklus einer bereits lauffähigen Anwendung.

Insbesondere:

```text
CONSOLIDATOR
    Source Architecture

DEPLOYER
    Release Architecture
```

---

## 101A.3 Zielstruktur

Mindestens folgende Struktur vorsehen:

```text
src/auditcore.tools.deployer/
├── __init__.py
├── cli.py
├── config.py
├── models/
│   ├── application.py
│   ├── build.py
│   ├── package.py
│   ├── runtime.py
│   └── deployment.py
│
├── discovery/
│   ├── application.py
│   ├── python.py
│   ├── frontend.py
│   ├── services.py
│   └── dependencies.py
│
├── build/
│   ├── python.py
│   ├── frontend.py
│   ├── assets.py
│   └── manifest.py
│
├── debian/
│   ├── control.py
│   ├── filesystem.py
│   ├── maintainer_scripts.py
│   ├── systemd.py
│   ├── conffiles.py
│   └── package_builder.py
│
├── apt/
│   ├── repository.py
│   ├── metadata.py
│   ├── signing.py
│   └── publishing.py
│
├── validation/
│   ├── package.py
│   ├── install.py
│   ├── upgrade.py
│   ├── remove.py
│   └── health.py
│
├── providers/
│   ├── protocols.py
│   ├── local.py
│   ├── docker_testenv.py
│   └── kira.py
│
├── templates/
│   ├── debian/
│   └── systemd/
│
└── reporting/
```

---

## 101A.4 Ziel

Eine Anwendung wie `regulierung` soll ohne manuelle Spezialschritte in ein Debian-Paket überführt werden können.

Beispiel:

```bash
auditcore-deploy build regulierung
```

Erwartetes Ergebnis:

```text
dist/
    regulierung_1.0.0_amd64.deb
    regulierung_1.0.0_build-manifest.json
    regulierung_1.0.0_checksums.txt
```

---

## 101A.5 CLI

Mindestens:

```bash
auditcore-deploy inspect PATH
auditcore-deploy plan PATH
auditcore-deploy build PATH
auditcore-deploy test-package PACKAGE.deb
auditcore-deploy test-upgrade OLD.deb NEW.deb
auditcore-deploy apt-repo build DIST/
auditcore-deploy apt-repo publish DIST/
auditcore-deploy status
```

Zusätzlich:

```bash
auditcore-deploy build PATH --dry-run
auditcore-deploy build PATH --output DIST
auditcore-deploy build PATH --format json
```

---

## 101A.6 Programmatic API

Mindestens:

```python
from auditcore.tools.deployer import DeploymentBuilder

builder = DeploymentBuilder(...)
result = builder.build_application("regulierung")
```

sowie getrennte APIs für:

```text
ApplicationInspection
DeploymentPlan
DebianPackageBuild
PackageValidation
UpgradeValidation
AptRepositoryBuild
```

---

## 101A.7 Anwendungsbeschreibung

Jede deploybare Anwendung soll eine maschinenlesbare Deployment-Konfiguration besitzen.

Beispiel:

```yaml
application:
  name: regulierung
  version_source: pyproject
  service_name: regulierung

backend:
  type: python
  entrypoint: regulierung.main:app

frontend:
  type: vite
  source: frontend
  build_output: dist

runtime:
  user: regulierung
  group: regulierung
  workdir: /opt/regulierung

config:
  directory: /etc/regulierung

data:
  directory: /var/lib/regulierung

service:
  type: systemd
  port: 8000

health:
  url: http://127.0.0.1:8000/health
```

Format und Schema sind zu versionieren.

---

## 101A.8 Automatische Anwendungserkennung

`auditcore.tools.deployer` soll vorhandene Anwendungen soweit wie möglich automatisch analysieren.

Zu erkennen sind insbesondere:

```text
pyproject.toml
requirements*.txt
package.json
vite.config.*
Dockerfile
docker-compose.yml
alembic.ini
systemd files
environment examples
frontend directories
static builds
```

Das Ergebnis ist ein:

```text
ApplicationDeploymentProfile
```

Nicht eindeutig erkennbare Werte werden als:

`REVIEW_REQUIRED`

markiert.

---

## 101A.9 DeploymentPlan

Vor dem tatsächlichen Build ist ein strukturierter Plan zu erzeugen.

Mindestens:

```text
application
version
source_commit
backend_runtime
frontend_build
shared_library_versions
system_dependencies
filesystem_layout
service_definition
configuration_files
persistent_directories
health_check
package_architecture
upgrade_strategy
```

---

## 101A.10 Integration mit `auditcore.tools.quality`

Vor dem Paketbuild muss `auditcore.tools.deployer` vorhandene Qualitätsinformationen berücksichtigen.

Ein freigabefähiges Paket darf standardmäßig nicht erzeugt werden, wenn:

```text
auditcore.tools.quality = FAIL
```

oder verpflichtende Application Tests fehlschlagen.

Override nur explizit und maschinenlesbar dokumentiert.

---

## 101A.11 Integration mit `auditcore.tools.consolidator`

Der Consolidator darf nach erfolgreicher Konsolidierung einen Deployment-Handoff erzeugen.

Beispiel:

```json
{
  "application": "regulierung",
  "status": "READY_FOR_DEPLOYMENT",
  "git_commit": "...",
  "shared_libraries": {
    "auditcore": "0.4.0"
  },
  "quality_status": "PASS"
}
```

`auditcore.tools.deployer` kann diesen Handoff als Input verwenden.

Damit bleibt die Grenze zwischen Source-Konsolidierung und Deployment eindeutig.

---

## 101A.12 Build ohne Zielserver-Zugriff

Das `.deb` muss grundsätzlich gebaut werden können, ohne auf dem Zielserver Änderungen vorzunehmen.

Ziel:

```text
Build System / CI
      ↓
fertiges .deb
      ↓
Zielserver
```

---

## 101A.13 Offline-Fähigkeit

Das erzeugte `.deb` bzw. ein dazugehöriger Paket-Bundle muss so aufgebaut sein, dass während der eigentlichen Installation keine unkontrollierten Downloads von PyPI oder npm erforderlich sind.

Abhängigkeiten müssen:

- als Debian-Abhängigkeit,
- als mitgelieferte Wheels,
- oder als vorgebaute Artefakte

auflösbar sein.

---

## 101A.14 Paketierungsstrategien

`auditcore.tools.deployer` soll unterschiedliche Strategien unterstützen.

Mindestens:

```text
DEBIAN_NATIVE_PYTHON
BUNDLED_VENV
WHEELHOUSE
STATIC_FRONTEND
EXTERNAL_DATABASE
SYSTEMD_SERVICE
```

Die Strategie ist pro Anwendung explizit im DeploymentPlan festzuhalten.

---

## 101A.15 Wiederverwendbare Templates

Debian- und systemd-Dateien dürfen nicht pro Anwendung manuell neu geschrieben werden.

`auditcore.tools.deployer` soll versionierte Templates bereitstellen für:

```text
debian/control
debian/rules
debian/changelog
debian/conffiles
systemd unit
environment file
maintainer scripts
```

Anwendungsspezifische Werte werden aus dem DeploymentProfile eingesetzt.

---

## 101A.16 Debian Quality Gate

Zusätzlich zu `auditcore.tools.quality` erhält der Deployer eigene Prüfkennungen.

Beispielsweise:

```text
ACD-PKG-001    Paketstruktur
ACD-DEP-001    Debian Dependencies
ACD-CONF-001   Konfigurationstrennung
ACD-DATA-001   Persistente Daten
ACD-SVC-001    systemd
ACD-SEC-001    Service User / Rechte
ACD-BUILD-001  reproduzierbarer Build
ACD-INST-001   Installation
ACD-UPG-001    Upgrade
ACD-RM-001     Remove
ACD-HEALTH-001 Health Check
ACD-APT-001    APT Metadata
ACD-SIGN-001   Repository Signing
```

Statuswerte:

```text
PASS
FAIL
WARNING
REVIEW_REQUIRED
NOT_EXECUTED
NOT_CONFIGURED
```

---

## 101A.17 Eigene State Machine

`auditcore.tools.deployer` besitzt eine eigene State Machine:

```text
CREATED
APPLICATION_INSPECTED
DEPLOYMENT_PLAN_CREATED
QUALITY_VERIFIED
BACKEND_BUILT
FRONTEND_BUILT
PACKAGE_STAGED
DEB_BUILT
PACKAGE_VALIDATED
INSTALL_TESTED
UPGRADE_TESTED
HEALTH_CHECKED
APT_READY
PUBLISHED
COMPLETE
FAILED
```

Ein Paket darf nicht `COMPLETE` werden, wenn verpflichtende Installations- oder Health-Checks fehlschlagen.

---

## 101A.18 Tests des Deployers

Mindestens Tests für:

- Application Discovery
- Deployment Profile
- DeploymentPlan
- Python Packaging
- Frontend Build Detection
- Filesystem Layout
- systemd Generation
- Debian Metadata
- Maintainer Scripts
- Build Manifest
- Package Build
- Install Test
- Upgrade Test
- Remove Test
- Health Check
- Proxy Handling
- APT Metadata
- Signing Interface
- CLI
- JSON Reporting
- State Machine

---

## 101A.19 Fake-/Testumgebung

Tests dürfen keinen echten Behördenserver benötigen.

Für Installations- und Upgradeprüfungen ist eine saubere isolierte Debian-/Ubuntu-Testumgebung vorzusehen.

Bevorzugt:

- Container,
- disposable VM,
- vergleichbare isolierte Testumgebung.

Die reale Zielumgebung wird erst nach erfolgreichem Pakettest verwendet.

---

## 101A.20 KIRA-Anbindung

`auditcore.tools.deployer` darf Releasewissen nach KIRA schreiben.

Dokumenttypen mindestens:

```text
APPLICATION_RELEASE
PACKAGE_BUILD
DEPLOYMENT_PLAN
DEPLOYMENT
```

KIRA bleibt hierbei Wissensspeicher, nicht Paketquelle.

---

## 101A.21 Verantwortlichkeitsmodell der vier Bibliotheken

```text
                  GitHub Repositories
                          │
                          ▼
               auditcore.tools.consolidator
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
        auditcore              Shared Libraries
             │                         │
             └────────────┬────────────┘
                          ▼
              auditcore.tools.apprefactor
                          │
                          ▼
               Fachanwendungen
                          │
                          ▼
              auditcore.tools.quality
                          │
                          ▼
                 READY_FOR_DEPLOYMENT
                          │
                          ▼
                auditcore.tools.deployer
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
           .deb                   APT Repository
             │                         │
             └────────────┬────────────┘
                          ▼
                     Zielserver
```

---

## 101A.22 Leitprinzip des Deployers

```text
CONSOLIDATE FIRST.
TEST SECOND.
PACKAGE THIRD.
DEPLOY LAST.
```

`auditcore.tools.deployer` darf keine schlechte oder ungeprüfte Anwendungsarchitektur dadurch "lösen", dass sie lediglich paketiert wird.


# 102A. Zweites Hauptziel: vollständige Anwendungen per APT deployen

Nach der Konsolidierung und Optimierung der Bibliotheken und Fachanwendungen soll die Plattform zusätzlich die vollständige Bereitstellung von Anwendungen auf Debian-/Ubuntu-Systemen unterstützen.

Das Ziel ist, eine fertige Fachanwendung beispielsweise mit:

```bash
sudo apt update
sudo apt install regulierung
```

installieren zu können.

Updates sollen später grundsätzlich über:

```bash
sudo apt update
sudo apt upgrade
```

möglich sein.

---

# 102B. Zielumgebung

Als Zielumgebung ist mindestens ein virtualisierter Debian-/Ubuntu-Server zu unterstützen.

Ausgangslage des derzeit vorgesehenen Servers:

- standardmäßig installiertes Linux-System,
- SSH-Zugriff,
- Zugriff über das Behördennetz beziehungsweise einen zugelassenen Remote-Zugang,
- eingerichteter Proxy,
- Paketinstallation und Paketupdates über `apt`,
- keine Annahme zusätzlicher vorinstallierter Anwendungsframeworks.

Der Deploymentprozess darf daher nicht voraussetzen, dass Docker, Node.js, Poetry, uv, npm oder andere Entwicklungswerkzeuge bereits auf dem Zielserver vorhanden sind.

Zusätzliche Laufzeitkomponenten müssen entweder:

1. als APT-Abhängigkeit installiert werden oder
2. Bestandteil des Anwendungspakets sein.

---

# 102C. Deployment-Prinzip

Entwicklung und Zielserver sind zu trennen.

Der Zielserver soll keine Entwicklungsumgebung benötigen.

Bevorzugter Ablauf:

```text
GitHub
   ↓
CI / Build
   ↓
Tests
   ↓
auditcore.tools.quality
   ↓
Application Integration Tests
   ↓
Build-Artefakte
   ↓
Debian Package (.deb)
   ↓
APT Repository oder Dateiübertragung
   ↓
Zielserver
   ↓
apt install / apt upgrade
```

Auf dem Produktiv- beziehungsweise Pilotserver soll kein Source-Build erforderlich sein.

---

# 102D. Paketierungsziele

Für gemeinsame Bibliotheken und Anwendungen sind mindestens folgende Artefakte vorzusehen:

## Python-Bibliotheken

```text
Wheel (.whl)
Source Distribution (.tar.gz)
```

zusätzlich, soweit für die Zielumgebung sinnvoll:

```text
Debian Package (.deb)
```

## Vollständige Anwendungen

Mindestens:

```text
Debian Package (.deb)
```

Optional zusätzlich:

```text
APT Repository
Container Image
```

Containerisierung ist optional und darf für die erste Installation nicht zwingend vorausgesetzt werden.

---

# 102E. Debian-Paket einer Fachanwendung

Eine vollständige Fachanwendung wie `regulierung` soll als eigenständiges Paket installierbar sein.

Beispiel:

```text
regulierung_1.0.0_amd64.deb
```

Installation:

```bash
sudo apt install ./regulierung_1.0.0_amd64.deb
```

Später über Repository:

```bash
sudo apt install regulierung
```

---

# 102F. Ziel-Dateisystem einer Anwendung

Für serverseitige Anwendungen ist grundsätzlich eine Linux-konforme Struktur vorzusehen.

Beispiel:

```text
/opt/regulierung/
    application/
    frontend/
    runtime/

/etc/regulierung/
    regulierung.toml
    regulierung.env

/var/lib/regulierung/
    data/
    uploads/
    generated/
    cache/

/var/log/regulierung/
    optional, sofern nicht ausschließlich journald verwendet wird

/usr/lib/systemd/system/
    regulierung.service
```

Anwendungscode, Konfiguration und persistente Daten dürfen nicht vermischt werden.

---

# 102G. Konfiguration

Konfigurationen gehören grundsätzlich nach:

```text
/etc/<application>/
```

Sie dürfen bei einem normalen:

```bash
apt upgrade
```

nicht unkontrolliert überschrieben werden.

Credentials dürfen nicht fest im Debian-Paket enthalten sein.

Unterstützt werden sollen beispielsweise:

- Environment-Datei,
- Konfigurationsdatei,
- Secret Store,
- systemd EnvironmentFile.

---

# 102H. Persistente Daten

Persistente Daten gehören grundsätzlich nach:

```text
/var/lib/<application>/
```

Ein Upgrade darf diese Daten nicht löschen.

Ein Entfernen des Pakets mit:

```bash
apt remove
```

soll persistente Daten grundsätzlich erhalten.

Ein vollständiges Löschen darf nur bei:

```bash
apt purge
```

und auch dort nur kontrolliert erfolgen.

---

# 102I. Systemd-Integration

Serveranwendungen sollen als `systemd`-Dienst installierbar sein.

Beispiel:

```bash
sudo systemctl status regulierung
sudo systemctl restart regulierung
sudo systemctl enable regulierung
```

Das Debian-Paket soll die erforderliche Unit-Datei bereitstellen.

Dienststart nach Installation muss konfigurierbar sein.

---

# 102J. Frontend-Build

Bei Webanwendungen darf der Zielserver keinen Node.js-Build durchführen müssen.

Frontend-Artefakte sind bereits im CI-/Buildprozess zu erzeugen.

Der `.deb`-Build enthält die fertigen statischen Assets.

Beispiel:

```text
React/Vue Source
       ↓
CI npm build
       ↓
dist/
       ↓
Debian Package
       ↓
Target Server
```

---

# 102K. Python-Runtime und Abhängigkeiten

Der Installationsprozess darf nicht ungeprüft `pip install` in das systemweite Python ausführen.

PEP-668-konforme Systeme sind zu berücksichtigen.

Zulässige Strategien sind insbesondere:

1. echte Debian-Python-Pakete über `dh-python` / `pybuild`,
2. isolierte anwendungsspezifische Python-Laufzeit,
3. offline installierbarer, versionierter Wheel-Bestand im Anwendungspaket.

Welche Strategie verwendet wird, ist pro Anwendung zu dokumentieren.

Der Paketinstallationsprozess darf nicht davon abhängen, dass PyPI vom Zielserver erreichbar ist.

---

# 102L. Shared Libraries im Deployment

Die Quellcode-Konsolidierung und die Laufzeitverteilung sind getrennte Fragestellungen.

Alle Fachanwendungen sollen dieselbe definierte Version der gemeinsamen Bibliotheken verwenden können.

Dies kann beispielsweise erfolgen durch:

```text
auditcore Python Wheel
```

als Build-Abhängigkeit der Fachanwendung oder durch ein separates Debian-Paket.

Die gewählte Strategie muss:

- reproduzierbar,
- versioniert,
- testbar,
- offline installierbar

sein.

Unkontrollierte Downloads während `postinst` sind zu vermeiden.

---

# 102M. Anwendungsabhängigkeiten

Das Debian-Paket muss erforderliche Systemabhängigkeiten deklarieren.

Beispielhaft:

```text
python3
python3-venv
ca-certificates
postgresql-client
```

Nur tatsächlich benötigte Abhängigkeiten aufnehmen.

Anwendungsspezifische Python-Pakete sollen reproduzierbar versioniert sein.

---

# 102N. Datenbankmigrationen

Falls eine Anwendung Datenbankmigrationen benötigt:

- Migrationen müssen versioniert sein,
- Upgrade-Reihenfolge muss definiert sein,
- Datenverlust ist zu vermeiden,
- fehlgeschlagene Migrationen müssen erkennbar sein.

Automatische Migration während `apt upgrade` darf nur erfolgen, wenn sie sicher und reproduzierbar ist.

Andernfalls ist ein expliziter Migrationsschritt vorzusehen.

---

# 102O. Installationsskripte

Debian-Paketierung darf bei Bedarf folgende Skripte nutzen:

```text
preinst
postinst
prerm
postrm
```

Diese müssen:

- idempotent,
- nachvollziehbar,
- fehlertolerant

sein.

Keine versteckten externen Downloads.

---

# 102P. Anwendungssystemkonto

Serverdienste sollen nach Möglichkeit nicht als `root` laufen.

Bei Bedarf soll das Debian-Paket einen dedizierten Benutzer erzeugen, beispielsweise:

```text
regulierung
```

mit minimal erforderlichen Rechten.

---

# 102Q. Reverse Proxy und Ports

Die Anwendung muss dokumentieren:

- internen Listen-Port,
- Health-Endpoint,
- erforderliche eingehende Ports,
- erforderliche ausgehende Verbindungen.

Eine Reverse-Proxy-Konfiguration kann optional bereitgestellt werden.

Sie darf bestehende Serverkonfigurationen nicht ungefragt überschreiben.

---

# 102R. Proxy-Fähigkeit

Da die Zielumgebung einen Proxy verwendet, müssen Build- und Laufzeitkomponenten Proxy-Konfigurationen respektieren können.

Mindestens berücksichtigen:

```text
HTTP_PROXY
HTTPS_PROXY
NO_PROXY
```

Der normale Betrieb einer fertig installierten Fachanwendung soll jedoch nicht unnötig von externem Internetzugriff abhängen.

---

# 102S. APT-Repository

Als spätere Ausbaustufe soll ein eigenes signiertes APT-Repository unterstützt werden.

Zielbild:

```text
APT Repository
├── auditcore
├── regulierung
├── flowaudit
├── audit-designer
└── weitere Anwendungen
```

Installation:

```bash
sudo apt update
sudo apt install regulierung
```

Das Repository muss signiert werden.

Repository-URL und Schlüssel dürfen nicht hart im Anwendungscode verankert sein.

---

# 102T. Paketversionen

Anwendungen und Bibliotheken müssen eigenständige Versionen besitzen.

Beispiel:

```text
auditcore 0.4.0
regulierung 1.2.0
```

Zu jedem Anwendungspaket muss nachvollziehbar sein:

- welche `auditcore`-Version verwendet wurde,
- welcher Git-Commit gebaut wurde,
- welche CI-Ausführung das Paket erstellt hat,
- welche Tests bestanden wurden.

---

# 102U. Build Manifest

Jedes Anwendungspaket soll ein maschinenlesbares Build-Manifest enthalten.

Mindestens:

```json
{
  "application": "regulierung",
  "version": "1.2.0",
  "git_commit": "...",
  "auditcore_version": "0.4.0",
  "built_at": "...",
  "quality_status": "PASS"
}
```

Optional weitere Shared Libraries.

---

# 102V. Deployment-Quality-Gate

Vor Erstellung eines freigabefähigen `.deb` müssen mindestens erfolgreich sein:

```text
Unit Tests
Regression Tests
Integration Tests
Ruff
Type Checking
Security Checks
auditcore.tools.quality
Application-specific Quality Gates
Frontend Build
Package Build
Package Installation Test
Application Health Check
```

---

# 102W. Testinstallation in sauberer Umgebung

Jedes `.deb` soll automatisiert in einer sauberen Debian-/Ubuntu-Testumgebung installiert werden.

Mindestens testen:

```bash
apt install ./application.deb
systemctl status <application>
```

sowie einen anwendungsspezifischen Health Check.

Danach zusätzlich testen:

```bash
apt remove <application>
```

und, soweit vorgesehen:

```bash
apt upgrade
```

---

# 102X. Deployment Status in KIRA

KIRA soll zusätzlich speichern können:

```text
APPLICATION_RELEASE
PACKAGE_BUILD
DEPLOYMENT
```

Beispiel:

```text
Application:
regulierung

Version:
1.2.0

Git Commit:
...

auditcore:
0.4.0

Package:
regulierung_1.2.0_amd64.deb

Quality:
PASS

Deployment:
INSTALLED

Target:
pilot-server
```

Keine Secrets, Kennwörter oder vertraulichen Serverzugangsdaten in KIRA speichern.

---

# 102Y. Neuer Gesamtworkflow

Der vollständige Lebenszyklus lautet:

```text
1. GLOBAL INVENTORY
        ↓
2. KIRA KNOWLEDGE BASE
        ↓
3. LIBRARY CANDIDATE DETECTION
        ↓
4. CHARACTERIZATION
        ↓
5. auditcore / Shared Library
        ↓
6. BIBQUALITY
        ↓
7. AUDITCORE_APPREFACTOR
        ↓
8. APPLICATION MIGRATION
        ↓
9. APPLICATION OPTIMIZATION
        ↓
10. REGRESSION + INTEGRATION TESTS
        ↓
11. APPLICATION PACKAGE BUILD
        ↓
11. DEBIAN PACKAGE TEST
        ↓
12. APT DEPLOYMENT
        ↓
13. HEALTH CHECK
        ↓
14. INVENTORY + KIRA UPDATE
```

---

# 102Z. Reihenfolge der Umsetzung durch Codex

Codex soll die Gesamtplattform in folgender Priorität umsetzen:

## Phase A – Grundlage

1. `auditcore`
2. `auditcore.tools.quality`
3. `auditcore.tools.consolidator`
4. Tests und CI

## Phase B – Softwareinventur

5. GitHub-Gesamtinventur
6. KIRA-Synchronisierung
7. Graphify-Analyse
8. Bibliothekskandidaten

## Phase C – Konsolidierung

9. erste gemeinsame Bibliotheksfunktionen erstellen
10. `auditcore.tools.apprefactor` implementieren
11. Fachanwendungen auf Shared Libraries migrieren
12. Fachanwendungen strukturell und technisch optimieren
13. Regression und Integration testen

## Phase D – Deployment

14. `auditcore.tools.deployer` implementieren
15. Debian-Paketierungsframework erstellen
16. zunächst eine reale Fachanwendung vollständig paketieren
17. Installation in sauberer Testumgebung prüfen
18. Upgrade-Pfad prüfen
19. anschließend weitere Anwendungen paketierbar machen

Die Paketierung darf die Bibliothekskonsolidierung nicht ersetzen.

Sie baut auf der zuvor konsolidierten und getesteten Anwendungsarchitektur auf.

---

# 102AA. Zusätzliche Definition of Done für eine paketierte Anwendung

Eine Fachanwendung gilt erst als deploybar, wenn:

- reproduzierbarer Build existiert,
- Frontend vorgebaut ist,
- Backend-Laufzeit reproduzierbar ist,
- keine Build-Tools auf dem Zielserver erforderlich sind,
- `.deb` erfolgreich gebaut wird,
- `.deb` in sauberer Testumgebung installiert wird,
- Konfiguration sauber getrennt ist,
- Daten bei Upgrade erhalten bleiben,
- systemd-Dienst funktioniert,
- Health Check funktioniert,
- Logs verfügbar sind,
- Upgrade getestet wurde,
- Entfernung getestet wurde,
- verwendete `auditcore`-Version dokumentiert ist,
- Build Manifest vorhanden ist,
- Deploymentstatus in KIRA geschrieben werden kann.

---

# 102AB. Ergebnisziel

Das Endziel ist nicht nur:

```text
auditcore exists
```

sondern:

```text
bestehende Repositories
        ↓
weniger duplizierter Code
        ↓
gemeinsame getestete Bibliotheken
        ↓
schlankere Fachanwendungen
        ↓
optimierte Anwendungen
        ↓
reproduzierbare Debian-Pakete
        ↓
Installation per apt
```

Beispiel:

```bash
sudo apt update
sudo apt install regulierung
```

Damit soll eine neue oder aktualisierte Fachanwendung ohne manuelle Source-Code-Installation auf einem vorgesehenen Linux-Server bereitgestellt werden können.

---

# 103. Verbindliche Abschlussprüfung durch Codex

Codex beendet die Aufgabe nicht nach dem Schreiben des Codes.

Tatsächlich ausführen:

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy src
auditcore-bibquality src/auditcore --strict
auditcore-bibquality src/auditcore.tools.quality
auditcore-bibquality src/auditcore.tools.consolidator
auditcore-bibquality src/auditcore.tools.apprefactor
auditcore-bibquality src/auditcore.tools.deployer
auditcore-bibquality --help
auditcore-consolidate --help
auditcore-refactor --help
auditcore-deploy --help
```

Wenn ein Befehl scheitert:

1. Fehler analysieren
2. korrigieren
3. erneut ausführen

Wiederholen, bis alle verpflichtenden Prüfungen erfolgreich sind oder ein technisch begründeter Blocker vorliegt.

---

# 104. Verbindlicher Abschlussbericht

Am Ende ausgeben:

```text
AUDITCORE PLATFORM BUILD REPORT

Version:
Git Commit:

Installation:
PASS / FAIL

pytest:
...

Ruff:
...

Mypy:
...

auditcore BibQuality:
...

auditcore.tools.quality Self Check:
...

auditcore.tools.consolidator Self Check:
...

auditcore.tools.apprefactor Self Check:
...

auditcore.tools.deployer Self Check:
...

Deployment Packaging:
...

GitHub Inventory:
...

Framework Policy Source:
...

Policy Evaluation:
...

KIRA:
...

Graphify:
...

Inventory Files:
...

Prompts:
...

Policies:
...

Coverage:
...

Neue Dateien:
...

Geänderte Dateien:
...

Offene Punkte:
...

Blocker:
...
```

Keine erfundenen Ergebnisse.

---

# 105. Git-Commit

Wenn Git verfügbar und die Änderungen erfolgreich geprüft wurden:

```text
feat: initialize auditcore platform with inventory, consolidation and quality gates
```

Keine History-Rewrites.

---

# 106. Initialer Codex-Startbefehl

Codex soll nach Lesen dieses Dokuments wie folgt beginnen:

## Schritt 1

Analysiere das aktuelle Repository und prüfe, ob bereits Komponenten von:

```text
auditcore
auditcore.tools.quality
auditcore.tools.consolidator
auditcore.tools.deployer
```

existieren.

## Schritt 2

Implementiere fehlende technische Grundlagen vollständig.

## Schritt 3

Installiere und teste die Plattform.

## Schritt 4

Wenn GitHub-Zugriff für den authentifizierten Benutzer verfügbar ist:

Starte:

`GLOBAL INITIAL INVENTORY`

und inventarisiere alle relevanten Repositories.

## Schritt 5

Speichere das Inventar lokal und synchronisiere es mit KIRA, sofern KIRA konfiguriert ist.

## Schritt 6

Verwende Graphify für relevante Abhängigkeitsanalysen, sofern verfügbar.

## Schritt 7

Erzeuge einen initialen Bericht über:

- Repositorylandschaft
- interne Bibliotheken
- Duplikate
- semantische Ähnlichkeiten
- Bibliothekskandidaten
- mögliche `auditcore`-Domains
- potenzielle Consumer
- technische Konflikte
- fachliche Konflikte
- Migrationskandidaten

## Schritt 8

Führe nicht automatisch eine unkontrollierte Komplettmigration durch.

Arbeite anschließend komponentenweise.

## Schritt 9

Für jeden eindeutig geeigneten Kandidaten:

```text
Characterize
→ Consolidate
→ Test
→ BibQuality
→ Migrate Consumer
→ Integration Test
→ Update Inventory
→ Update KIRA
```

## Schritt 10

Beende erst nach dem vollständigen Build- und Statusbericht.

---

# 107. Zielbild

Nach erfolgreicher Umsetzung soll eine spätere Aufgabe wie:

> Ich brauche im Audit-Designer eine neue Dokumentenprüfung.

nicht unmittelbar neuen isolierten Code erzeugen.

Das System soll zunächst prüfen:

```text
Audit-Designer
    ↓
lokale Implementierungen
    ↓
auditcore
    ↓
Shared Libraries
    ↓
KIRA
    ↓
GitHub-Quellen
    ↓
Graphify
    ↓
Reuse / Extend / Consolidate / Local Implementation
```

Damit wird die Softwarelandschaft systematisch weiterentwickelt, anstatt bei jeder Anwendung erneut ähnliche Funktionen zu erzeugen.

---

# 108. Endgültige Leitformel

```text
GITHUB TELLS US WHAT EXISTS.

KIRA REMEMBERS WHAT WE KNOW ABOUT IT.

THE FRAMEWORK DEFINES GENERAL SECURITY, ARCHITECTURE AND GOVERNANCE REQUIREMENTS.

AUDITCORE EVALUATES THEIR APPLICABILITY BEFORE ENFORCING THEM.

GRAPHIFY TELLS US HOW IT IS CONNECTED.

AUDITCORE HOLDS THE SHARED DOMAIN LOGIC AND THE LOGICALLY SEPARATED TOOLING.

BIBQUALITY ENFORCES TECHNICAL QUALITY.

THE CONSOLIDATOR CONTROLS THE WORKFLOW.

THE LLM HELPS WITH SEMANTIC ANALYSIS.

THE HUMAN DECIDES DOMAIN, LEGAL AND POLICY QUESTIONS.
```
