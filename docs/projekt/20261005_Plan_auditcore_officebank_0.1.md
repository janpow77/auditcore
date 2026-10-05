# Plan: `auditcore_officebank` – Office-, VBA- und VM-Prüfbank mit Claude-Code-Plugin

Fassung 0.1 · Stand 05.10.2026 · Status: **freigegeben am 05.10.2026** (alle Entscheidungen wie empfohlen; Etappe 0 umgesetzt)

Dieses Dokument liegt im öffentlichen auditcore-Repository. Es nennt deshalb weder
Behörden noch Personen, Daten, Rechnernamen, Adressen, Ordner-IDs oder private
Pfade. Die vier Pilotprojekte, aus denen die Vorgehensweisen stammen, heißen hier
nur **P-ACC** (Access-Auswertungsdatenbank mit Berichten, Diagrammen und
Word-Dossier), **P-XL1** und **P-XL2** (zwei Excel-Makroprojekte mit
Ergebnismappen und Diagrammen) und **P-PROT** (Access-Datenbank, die
Word-Protokolle ausliest). Dazu kommt ein **QChess-Testdienst** (SQL Server im
Container und QChess-Client in der VM).

---

## 1 Zielbild und Abgrenzung

### 1.1 Ausgangslage

Am 05.10.2026 liefen alle vier Pilotprojekte erstmals nativ in einer
Windows-11-VM (UTM auf macOS, Office 365 64 Bit, deutsch). Der Weg dahin bestand
aus rund 40 Einzelskripten: Bash- und AppleScript-Wrapper auf dem Mac,
PowerShell-Gastskripte, Python-Gates und Abnahmeskripte je Projekt. Sie wurden
von Projekt zu Projekt kopiert und angepasst. Die Vorgehensweise hat sich
bewährt: erst Gates, dann MCP-Vorlauf, dann nativer Lauf, dann Abnahme gegen
unabhängige Sollwerte und am Ende ein datenfreies Lieferpaket. Die Werkzeuge
selbst sind aber nicht wiederverwendbar. Rechnernamen, Benutzernamen,
Testordner und Projektkürzel stehen fest im Code.

### 1.2 Ziel

1. **Bibliothek `auditcore_officebank`** (Python ≥ 3.11, Kern nur
   Standardbibliothek): Die bewährten Abläufe werden als getestete, konfigurierbare
   Bausteine mit einer CLI `auditcore-officebank` bereitgestellt. Gastskripte
   (PowerShell) und Mac-Skripte (AppleScript) liegen als Paketdaten bei.
2. **Claude-Code-Plugin `auditcore-office`**: Skills (Arbeitsabläufe als
   Slash-Befehle), Agenten-Definitionen mit festen Regeln, Hooks und Vorlagen.
   Das Plugin ruft die CLI auf und enthält selbst keine Logik.
3. **Runner-Profile** `vba`, `access`, `office` für `auditcore-runner`, damit
   dieselben Gates lokal, im Pre-push-Hook und im Agentenlauf mit einheitlichen
   Befunden laufen.

### 1.3 Abgrenzung

| Ebene | gehört hierher | gehört nicht hierher |
|---|---|---|
| **auditcore_officebank** (öffentlich) | VM-Steuerung, Office-Automation (Excel, Access, Word), Build, Gates, Abnahme-Mechanik, Paketbau, generischer SQL-Server-Testdienst | Fachlogik, Sollwerte, Projektnamen, Namenslisten, echte Daten, Rechner-/Netzangaben |
| **Plugin `auditcore-office`** (öffentlich) | Abläufe, Agentenrollen, Regeln, Vorlagen, Hooks | Projektentscheidungen, Projekt-Agentenregeln |
| **Projekt-Repos** (privat) | `src/` (VBA, SQL, Texte), `.officebank.toml`, `sollwerte.py`/`sollwerte.json`, begründete Abweichungen, Plan mit Nutzerentscheidungen, `SCHNITTSTELLEN.md`, `MODULLISTE.md`, Projektprofile (z. B. QChess-Client) | – |
| **Rechnerprofil** (`~/.config/auditcore-officebank/profil.toml`) | VM-Name, Hostnetz, SSH-Ziele, MCP-Endpunkte, Schlüsselbund-Einträge, rclone-Remote, Kopfkommentar des Autors | – |

**Verhältnis zu `auditcore_runner`:** Der Runner bleibt die Prüfbank für
Quellcode. Er führt die Gates der officebank als eigene Werkzeuge aus (Bereich
`eigen`, JUnit über `{ausgabe}`) und vereinheitlicht ihre Befunde
(Fingerabdruck, Baseline, Aufgabenpaket). Die officebank bringt keine eigene
Befundverwaltung mit. Native Office-Läufe sind **kein** Runner-Werkzeug im Image,
weil Office nicht in einen Container passt. Sie laufen als eigenes Profil `nativ`
nur auf Rechnern mit VM (Kap. 3).

**Verhältnis zum FlowAudit-MCP:** Der MCP prüft statisch (`vba_check_*`,
`vba_kompilieren`, `access_check_*`, `vba_session_*`). Die officebank ist dafür
nur **Client**: Sie baut die Nutzlast, beachtet Sitzung, Manifest-Hash,
Paginierung, Zeitlimit und Teilmengen und legt den Nachweis ab. Prüfregeln
gehören in den MCP. Die Lücken aus den nativen Läufen stehen im
MCP-Lückenpapier vom 05.10.2026 (privates Repository). Umgekehrt liefert
die officebank, was dem MCP fehlt: den Manifest-Export aus der gebauten accdb
(`access.export_manifest`) und den nativen Gegenbeleg. Status-Regel ohne
Ausnahme: Bis zu einem tatsächlichen Office-Lauf gilt
`native_office_compile = not_run`.

**Verhältnis zu anderen auditcore-Paketen:** Maskierung und Pseudonyme kommen
aus `auditcore_privacy`. Dokumente aus Vorlagen erzeugt `auditcore_reporting`
(`templates`). Statistikfunktionen für Sollwerte (Wilson, Holm, BH …) liegen in
`auditcore_statistics`. Ressourcenvergabe für mehrere Agenten kann später
`auditcore_flow_agent` übernehmen. Gemeinsame Hilfen (Hash, JSON, Dateinamen)
kommen aus `auditcore_common`, nicht als Kopie.

---

## 2 Module der Bibliothek

Paketregeln (AGENTS.md): Bezeichner englisch, Doku und Meldungen deutsch;
Module höchstens 400 Zeilen, Funktionen höchstens 60 Zeilen, Komplexität
höchstens 10, `mypy --strict`, kein `Any`. CLI-Befehle sind deutsch, wie beim
Runner. Jeder Seiteneffekt (osascript, ssh, Gastbefehl, HTTP) läuft über eine
schmale Schnittstelle (`Protocol`), damit Tests mit Fakes ohne Office und ohne VM
auskommen.

```text
packages/auditcore_officebank/
  src/auditcore_officebank/
    config.py          Rechnerprofil + Projektdatei (.officebank.toml), Schema-Version, Migration
    vm/                backend.py (Protocol), utm.py, exchange.py, session.py, lock.py,
                       screen.py, keyboard.py, setup.py, guestfiles.py
    office/            excel.py, excel_mac.py, access.py, word.py, dialogs.py, steps.py
    mssql/             service.py, restore.py, client_config.py, export.py
    build/             plan.py, transfer.py, runlog.py
    acceptance/        targets.py, compare.py, justified.py, report.py
    gates/             ascii.py, lint_vba.py, lint_sql.py, privacy.py, mcp_client.py, mcp_gate.py,
                       evidence.py, junit.py
    delivery/          package.py, redact.py, upload.py
    project/           scaffold.py (Vorlagen), ownership.py (MODULLISTE-Abgleich)
    cli.py
    data/gast/*.ps1    Gastskripte (ASCII, versioniert, mit SHA-256 im Manifest)
    data/mac/*.applescript
    data/vorlagen/*.md, data/schemas/*.json
```

Die Fachbegriffe aus dem Auftrag werden so abgebildet: `abnahme` →
`acceptance`, `liefern` → `delivery`, `qchess` → `mssql` (generisch) plus
QChess-Profil im Projekt (Entscheidung E05).

### 2.1 `vm` – Windows-Gast steuern

**Zweck:** Befehle im Gast ausführen (als SYSTEM über den Gastagenten oder in
der angemeldeten Benutzersitzung, die Office mit Lizenz braucht), Dateien hin-
und zurückbringen, exklusiv sperren, Bildschirmfotos aufnehmen und Text tippen.

```python
class GuestBackend(Protocol):  # utm.UtmBackend, später libvirt; tests: FakeGuest
    def exec_system(self, ps: str, timeout_s: int) -> GuestResult: ...
    def type_scancodes(self, codes: Sequence[int]) -> None: ...
    def status(self) -> VmState: ...


@dataclass(frozen=True)
class GuestResult:
    exit_code: int | None
    output: str
    duration_s: float
    job_id: str


class ExchangeServer:  # HTTP nur auf dem Hostnetz, Token je Lauf
    def __init__(self, root: Path, bind: str, port: int, token: str) -> None: ...
    def serve_in_background(self) -> ContextManager[str]: ...  # liefert Basis-URL


class UserSession:  # Aufgabenplanung, LogonType Interactive
    def run(self, script: GuestScript, timeout_s: int) -> GuestResult: ...


class VmLock:  # Sperrdatei mit Besitzer, PID, Zeit, TTL
    def acquire(self, owner: str, purpose: str, ttl_s: int) -> LockToken: ...
    def release(self, token: LockToken) -> None: ...
    def inspect(self) -> LockInfo | None: ...


def guest_screenshot(session: UserSession, name: str) -> Path: ...  # im Gast, nicht vom Host
def scancodes_for(text: str, layout: str = "de") -> list[int]: ...  # {ENTER} {TAB} …
def write_guest_script(body: str, path: Path) -> None: ...  # UTF-8 mit BOM, CRLF
```

**CLI:**

```bash
auditcore-officebank vm status
auditcore-officebank vm sperre nehmen --zweck "Build b12"   # Exit 2, wenn belegt
auditcore-officebank vm sperre freigeben
auditcore-officebank vm system  skript.ps1 [--zeitlimit 120]   # SYSTEM
auditcore-officebank vm nutzer  skript.ps1 [--zeitlimit 3600]  # Benutzersitzung
auditcore-officebank vm foto    name.png
auditcore-officebank vm tippen  "text{ENTER}"
auditcore-officebank vm austausch starten|stoppen|leeren
auditcore-officebank vm einrichten office|vertrauensorte|ordner|mtu
auditcore-officebank vm pruefen      # Speicher, Docker, MTU, Uhrzeit, Gastagent, Austauschserver
```

**Festlegungen aus den Läufen:**

- **Gastagent:** `execute … with output capturing` liefert die Ausgabe
  unzuverlässig. Deshalb schickt das Gastskript seine Ausgabe immer per HTTP-POST
  an den Austauschserver, und der Host wartet auf die Datei. Kodiert wird mit
  `-EncodedCommand` (UTF-16LE, Base64).
- **Benutzersitzung:** Office-COM braucht die angemeldete Sitzung, denn die
  Lizenz hängt am Benutzer. Ablauf: Job-Datei über den Austauschserver
  ablegen, geplante Aufgabe (`Interactive`, `Highest`) registrieren und
  starten, auf die Rückmeldung warten. Danach die Aufgabe und die Job-Datei
  **immer** entfernen, auch bei Zeitüberschreitung.
- **Austauschserver** (Verbesserung gegenüber heute): Er bindet nur an die
  Host-Adresse des VM-Netzes. Jeder Lauf bekommt ein Zufalls-Token im Pfad
  oder Header. POST-Namen werden auf den Dateinamen reduziert, GET-Pfade
  dürfen das Austauschverzeichnis nicht verlassen. Nach dem Lauf wird das
  Verzeichnis geleert. Große Ergebnisse gehen als **ein ZIP mit SHA-256**
  zurück (`ZipFile`-API im Gast, nicht `Compress-Archive`, das `\` als
  Trenner schreibt).
- **SPICE-WebDAV-Freigabe** ist optional (Ordnerfreigabe in UTM, im Gast als
  Laufwerk). `vm einrichten freigabe` dokumentiert die manuellen Schritte und
  prüft danach Erreichbarkeit und Schreibrecht. Standard bleibt der
  Austauschserver, weil er sich ohne UI einrichten lässt.
- **Sperre:** Pro VM arbeitet nur ein Agent. Die Sperrdatei enthält Besitzer,
  Zweck, PID, Startzeit und TTL. Eine abgelaufene Sperre meldet
  `vm sperre pruefen` als „verwaist“. Freigegeben wird sie nur ausdrücklich
  (`--erzwingen`) und mit Protokolleintrag.
- **Bildschirm:** Fotos entstehen im Gast (`CopyFromScreen` → POST). Ein
  Host-Fenster-Screenshot zeigt oft ein eingefrorenes Bild. Klickkoordinaten
  werden DPI-bewusst umgerechnet (Faktor wird gemessen, nicht fest kodiert).
- **Tastatur:** AppleScript `input keystroke` verfälscht deutsche Zeichen und
  hängt vom Fokus ab. Deshalb wird über PC-AT-Scancodes getippt, mit Tabellen
  je Layout (`de`, `us`), Umschalt- und AltGr-Folgen und Sondertasten.
  Zeichen ohne Abbildung führen zu einem Fehler statt zu stillen Ersetzungen.
- **Einrichtung (`vm/setup.py`, dokumentierte Halbautomatik):** VM anlegen
  (Architektur, Speicher, Kerne, TPM, ISO-Laufwerke), OOBE mit lokalem Konto
  ohne Microsoft-Konto, Gastwerkzeuge, Office über ODT. Die ODT-Konfiguration
  wird aus Parametern erzeugt (Edition 64 Bit, Kanal, Sprache, ausgeschlossene
  Apps). `setup.exe` lädt der Gast bei Microsoft, sie wird nicht mitgeliefert.
  Die Lizenz entsteht durch die Anmeldung des Nutzers. Dazu kommen
  Vertrauenswürdige Speicherorte und `AccessVBOM` **nur** für die Testordner
  (keine globale Makrofreigabe) sowie die Ordner `C:\Automation`, Testordner
  und `C:\temp`.
- **Hinweise statt Automatik:** `vm pruefen` warnt bei wenig freiem
  Hostspeicher (Docker Desktop beenden), bei MTU-Problemen auf öffentlichen
  oder mobilen Uplinks (Gast-MTU 1280 empfohlen), bei gesperrtem Bildschirm
  (UI-Automation blockiert) und bei ISO-Lesezeichen, die nach dem Verschieben
  einer ISO ins Leere zeigen. Mehr als 4–6 Kerne bringen bei Access/VBA nichts,
  weil VBA einen Kern nutzt.

### 2.2 `office.excel` – Excel unter Windows und macOS

```python
@dataclass(frozen=True)
class ModuleSet:
    names: tuple[str, ...]
    source_dir: Path
    encoding: Literal["ascii"]


def to_import_files(mods: ModuleSet, out: Path) -> Manifest: ...  # CP1252 + CRLF, Attribute-Zeile 1
def excel_run(
    session: UserSession,
    workbook: str,
    *,
    replace: ModuleSet | None,
    macros: Sequence[MacroCall],
    dialog_rules: DialogRules,
    save: bool,
) -> RunLog: ...
def build_carrier_workbook(
    session: UserSession,
    template: str,
    target: str,
    mods: ModuleSet,
    version_row: Mapping[str, str],
) -> RunLog: ...
# macOS (excel_mac.py, nur UI-Skripting, kein COM):
def mac_replace_module(workbook: str, module: str, path: Path, anchor: str) -> None: ...
def mac_compile(workbook: str) -> MacCompileState: ...
def mac_run_macro(workbook: str, macro: str, watch: DialogRules) -> RunLog: ...
```

**CLI:** `excel import`, `excel kompilieren`, `excel lauf --makro … --regeln …`,
`excel traeger --vorlage … --ziel … --versionszeile zeile.json`,
`excel mac-probelauf` (Testkopie mit Ersatzklassen, siehe unten).

**Festlegungen:**

- Kompiliert wird über das VBE-Steuerelement 578 („Projekt kompilieren“).
  `Enabled = False` danach heißt kompiliert. Protokolliert werden die
  Verweise (`IsBroken`), die Module mit Zeilenzahl, die Excel-Version und der
  Build.
- Eine xlsm wird **nur über das Excel-Objektmodell** geändert. openpyxl
  zerstört Formulare und Schaltflächen und ist nur lesend erlaubt.
- **Mac-Probelauf als Testkopie:** `Scripting.Dictionary` gibt es auf dem Mac
  nicht. Ersetzt wird es durch eine mitgelieferte Klasse, die nur die genutzten
  Member nachbildet. Die ausgelieferte Fassung bleibt unverändert, und der
  Probelauf ersetzt den Windows-Lauf nicht.
- **Mac-Fallen als eingebaute Prüfungen** (`excel_mac.preflight()`): Bildschirm
  gesperrt (`IOConsoleLocked`), VBE im Entwurfsmodus (Titel „[Entwurf]“: dann
  laufen keine Makros, Excel muss neu starten), Excel-Sandbox fragt je Ordner
  nach (Quellkopie in einen freigegebenen Ordner legen), Zugriff auf
  `VBProject` per Makro wird verweigert, UserForm-Textfelder lassen sich nicht
  per Bedienungshilfe setzen.
- **Gebietsschema:** `NumberFormat` von Diagrammachsen und Datenbeschriftungen
  liest Excel landesspezifisch („#.##0“). Die Kontrolle läuft deshalb über das
  Chart-XML der gespeicherten Mappe (`c:numFmt`, Hilfsfunktion
  `chart_number_formats(xlsx)`), nicht über den Lesewert.

### 2.3 `office.access` – accdb aus Quellen bauen

```python
@dataclass(frozen=True)
class AccessBuild:
    database: str
    modules: ModuleSet
    queries_dir: Path | None
    texts_dir: Path | None
    steps: tuple[Step, ...]
    compact: bool
    new: bool


Step = Run | Count | Form | Report | Close | Photo | Wait  # Schrittsprache RUN/ZAHL/FORM/…


def access_build(session: UserSession, build: AccessBuild, rules: DialogRules) -> RunLog: ...
def query_load_order(sql_dir: Path) -> list[str]: ...  # topologisch, Zyklen = Fehler
def export_manifest(session: UserSession, database: str) -> AccessManifest: ...  # Schema des MCP
def manifest_from_source(src: Path) -> AccessManifest: ...  # DDL/CreateQueryDef statisch
def diff_manifests(static: AccessManifest, built: AccessManifest) -> list[ManifestDiff]: ...
```

**CLI:** `access bauen`, `access abfragen-reihenfolge`, `access manifest
--aus manifest.json`, `access manifest-diff`, `access komprimieren`,
`access lauf --schritte "RUN:X;ZAHL:t|krit;FORM:frm;BERICHT:rpt"`.

**Festlegungen:**

- Bei jedem Vollbau wird die accdb neu angelegt (`NewCurrentDatabase`). Danach
  werden die Module in der Reihenfolge der Modulliste importiert,
  `DoCmd.Save` je Modul, und kompiliert wird mit `RunCommand 126` sowie der
  Kontrolle `IsCompiled` vorher und nachher. Gelingt das nicht, liest das Skript
  die Fehlerstelle aus `VBE.ActiveCodePane.GetSelection` (Modul, Zeile, Code)
  und bricht ab, ohne Makros auszuführen.
- Abfragen werden aus `src/abfragen/*.sql` angelegt, je Datei eine. Der
  Kommentar `-- Beschreibung:` wird zur Eigenschaft `Description` (erst setzen,
  nur bei Fehler anfügen). Geladen wird in Abhängigkeitsreihenfolge.
- DAO-Schema und referentielle Integrität: Hilfsroutinen bleiben im
  VBA-Projekt (Vorlage `modXX_Modell`). Die officebank prüft nur das Ergebnis
  über den Manifest-Export (Tabellen, Felder, Indizes, Beziehungen, Abfragen,
  Formulare, Berichte mit RecordSource).
- **Berichte und Diagramme:** Fotos der Seitenansicht. PDF-Export nur am Ende
  und nur für geänderte Berichte. Das moderne Diagramm-Steuerelement lässt sich
  nur eingeschränkt per Code setzen. Dazu kommt ein Hinweisblatt mit den
  Eigenschaften, die nur über `CallByName` gehen.
- **Klickprobe:** Access-Schaltflächen findet UIA nicht. Echte Klicks gehen über
  das Formular-`Hwnd` → Kindfenster `OFormSub` → `ClientToScreen`, Twips/1440·DPI
  und `SetProcessDPIAware`. Bevorzugt wird ein Klicktest im VBA-Projekt über die
  OnClick-Ausdrücke (`erg_Klickprobe`).
- `DAO.DBEngine` und ACE-OLEDB direkt aus PowerShell hängen oder fehlen bei
  Click-to-Run. Zugriff deshalb immer über `Access.Application.DBEngine`.
  `Access.Run` mit Argument braucht `[ref]`.
- Komprimieren erfolgt am Ende über `CompactRepair` in eine Kopie, die
  anschließend ausgetauscht wird. Protokolliert wird die Größe vorher und
  nachher, dazu eine Warnung ab 1,5 GB (die Grenze liegt bei 2 GB).

### 2.4 `office.word` – Dokumente und Word-Automation

```python
def office_theme() -> OfficeTheme: ...  # Office-2023-Design: Aptos, Akzent 1 #156082 …
def new_document(theme: OfficeTheme) -> DocxBuilder: ...  # Extra [docx], python-docx
def word_run(session: UserSession, script: GuestScript) -> RunLog: ...
def word_processes(session: UserSession) -> list[ProcessInfo]: ...  # Vorher/Nachher-Kontrolle
```

**Festlegungen:**

- Vorlagenbasierte Dokumente (Vermerke, Dossiers) erzeugt
  `auditcore_reporting.templates`. Die officebank liefert nur Designwerte und
  einen schmalen `DocxBuilder` für Anleitungen und Abnahmeberichte im
  Office-Design (Überschriften, Tabellen mit Kopfzeile, Tausendertrenner).
  Projektspezifische Kopfzeilen (Referat, Bearbeiter) stehen in der
  Projektkonfiguration und nie im Paket.
- **Text mit Listennummern:** `Content.Text` enthält keine automatischen
  Listennummern. Die VBA-Vorlage liest deshalb absatzweise
  `Range.ListFormat.ListString` (Vorlage `WordDokumentText` im Paket als
  `.bas`-Muster).
- **Sauberes Beenden:** Beendet wird nur die selbst gestartete Instanz
  (`eigeneInstanz`), auf dem Normal- **und** dem Fehlerpfad, mit
  `Quit SaveChanges:=0`. Eine Word-Instanz des Nutzers bleibt unberührt.
  Der Lauf prüft `WINWORD.EXE` vorher und nachher und meldet
  übriggebliebene Prozesse als Befund.

### 2.5 `mssql` (QChess-Testdienst) – SQL Server im Container

```python
@dataclass(frozen=True)
class MssqlService:
    name: str
    bind_address: str
    port: int
    data_dir: Path
    backup_dir: Path
    edition: str = "Developer"


def render_compose(svc: MssqlService) -> str: ...  # Port nur an bind_address
def restore_plan(
    bak: str, db: str, files: Sequence[LogicalFile]
) -> list[str]: ...  # FILELISTONLY → MOVE
def app_login_sql(
    db: str, login: str, role: str = "db_owner"
) -> list[str]: ...  # ALTER USER … WITH LOGIN
def patch_connection_string(
    config_xml: Path, key: str, server: str, db: str, secret_ref: SecretRef
) -> Patch: ...  # Sicherung + Diff ohne Passwort
def export_view(view: str, columns: Sequence[str], out: Path) -> ExportReport: ...  # Positivliste
```

**CLI:** `mssql dienst schreiben --ziel <ordner>` (compose.yml, `.env`-Vorlage
mit Platzhaltern, LIESMICH), `mssql restore --bak … --db …`,
`mssql login --db … --login …`, `mssql client-konfig --profil qchess.toml`,
`mssql export --view … --spalten-datei positivliste.txt`.

**Festlegungen:**

- Der Port wird nur an eine VPN-/Tailnet-Adresse gebunden, nie an `0.0.0.0`.
  Startet Docker vor dem VPN, schlägt die Bindung fehl. `mssql pruefen` erkennt
  das, Abhilfe ist ein erneutes `compose up`.
- Secrets stehen nur in `.env` (Rechte 600) bzw. im Schlüsselbund. Das
  Hilfsskript übergibt das Passwort per Umgebungsvariable an `sqlcmd` und zeigt
  es nie an. Alle Ausgaben laufen durch die Maskierung (Kap. 6).
- Nach einem Restore sind die DB-Benutzer verwaist. Deshalb folgt
  `ALTER USER … WITH LOGIN` bzw. beim ersten Mal `CREATE USER`. Verwaiste
  Fremd-Principals werden nur gemeldet, nicht repariert.
- **QChess-Client** als Projektprofil (`qchess.toml`, privat): Konfigurationsdatei,
  Schlüssel der Verbindungszeichenfolge, Pflichtordner, Login-Konvention. Am
  05.10. beobachtet und als Prüfpunkte von `mssql client-konfig` übernommen:
  Der Client erkennt SQL Server nur am Schlüssel `Server=` (mit
  `Data Source=` fällt er auf einen anderen Anbieter zurück), er braucht einen
  festen Temp-Ordner, der Lokalmodus wird bei jedem Start überschrieben, und
  angemeldet wird mit dem Windows-Benutzernamen, der in der Benutzertabelle
  stehen muss. UI-Dump und Klicks laufen über das generische
  `office.dialogs.ui_dump()` (UIA). Passwortfelder werden nie gelesen.
- Exportiert wird nur über eine View mit **Positivliste** von Spalten, ohne
  Personenfelder und Freitexte. Der Export prüft die Spalten gegen die Liste
  und bricht bei Abweichungen ab.

### 2.6 `build` – inkrementell, nachvollziehbar, aus Commits

```python
@dataclass(frozen=True)
class BuildInput:
    path: str
    sha256: str
    kind: Literal["module", "query", "text", "data"]


def collect_inputs(
    repo: Path, rev: str, spec: ProjectSpec
) -> list[BuildInput]: ...  # git show <rev>:…
def plan_build(
    inputs: Sequence[BuildInput], last: BuildState | None, deps: DepGraph
) -> BuildPlan: ...
def run_build(plan: BuildPlan, runner: BuildRunner) -> BuildResult: ...
def fetch_result(zip_path: Path, sha256_file: Path, target: Path) -> SumsFile: ...  # SHA256SUMS.txt
```

**CLI:** `build plan [--voll]`, `build lauf <kennung> [--rev HEAD] [--nur-geaendert]`,
`build abholen`, `build laufzeiten` (langsamste Schritte).

**Festlegungen:**

- Gebaut wird **nur aus committeten Ständen** (`git show <rev>:<pfad>`),
  nie aus Arbeitsständen paralleler Agenten. Der Commit steht im
  Laufprotokoll und im Abnahmebericht.
- **Inkrementell:** Ein Modul wird nur bei geändertem SHA-256 neu importiert.
  Schritte und Berichte laufen nur, wenn sich ihre Eingaben geändert haben.
  Der Abhängigkeitsgraph wird in der Projektdatei deklariert (Schritt →
  Module/Abfragen/Tabellen). Der Vollaufbau bleibt jederzeit möglich und ist
  vor jeder Abnahme zur Freigabe Pflicht.
- **Laufzeitprotokoll je Schritt** (Start, Ende, Dauer, Rückgabe, HRESULT).
  `build laufzeiten` nennt die langsamsten Schritte. Bekannte Ursachen:
  Domänenfunktionen in Schleifen, fehlende Indizes.
- Ergebnisse kommen als ein ZIP mit SHA-256 zurück, entpackt nach
  `ergebnisse/JJJJMMTT_Lauf_<kennung>/` (nur lokal, nie versioniert), dazu
  `SHA256SUMS.txt`. Fotos landen bei der Abnahme.

### 2.7 `acceptance` – Abnahme gegen unabhängige Sollwerte

```python
@dataclass(frozen=True)
class Tolerances: count: float = 0; amount: float = 0.005; ratio: float = 5e-7
                  rel_stat: float = 1e-6; days: float = 0.5
def load_targets(path: Path) -> TargetSet: ...                 # sollwerte.json, Schema versioniert
def read_results(folder: Path, run_id: str | None) -> ResultSet: ...  # erg_*.csv/.xlsx, dt. Zahlen
def compare(targets: TargetSet, results: ResultSet, tol: Tolerances,
            justified: Sequence[Justification]) -> AcceptanceReport: ...
def render_report(rep: AcceptanceReport, *, insert_into: Path | None) -> str: ...  # AUTO-Marken
```

**CLI:** `abnahme pruefen --erg <ordner> --soll sollwerte.json [--begruendet
abweichungen.toml] --aus abnahme.json`, `abnahme bericht --abnahme abnahme.json
[--einsetzen bericht.md]`.

**Festlegungen:**

- Die Sollwerte entstehen **unabhängig** in Python aus den Rohdaten, also im
  Projekt-Repo und nicht in der officebank. Die officebank liefert Schema,
  Vergleich, Toleranzen und Bericht.
- Exportformat der Ergebnisse (Vertrag): `erg_Kennzahl(Lauf_ID, Bericht,
  Kennzahl, Wert[, Text])` und Tabellen mit Schlüsselfeldern. Zahlen in
  deutscher Schreibweise, Prozent und Wahr/Falsch werden robust gelesen.
- **Begründete Abweichungen** stehen in einer eigenen Datei (ID, Muster,
  Vergleich `keiner|alternativ`, Art, Grund). Ein Treffer wird zu `BEGRUENDET`,
  nicht zu `BESTANDEN`. Alternativ-Sollwerte (z. B. nach dokumentierter
  Quellkorrektur) liegen in einer zweiten Sollwertdatei.
- Rückgabe 0 = bestanden, 1 = Abweichungen, 2 = Pflichtwerte fehlen. Der
  Bericht enthält Commit, ZIP-Hash, Lauf-ID, Zähler und Klickprobe und wird
  zwischen `<!-- AUTO:abnahme:start -->` und `…:ende -->` eingesetzt.
- Pseudonyme: Weicht die Pseudonymvergabe in Office von der Referenz ab,
  übersetzt eine lokale Zuordnungsdatei mit HMAC-Schlüssel. Der Schlüssel liegt
  nie in der Datenbank und nie im Repo.

### 2.8 `gates` – vor jeder Weitergabe von Code

| Gate | Funktion | Ergebnis |
|---|---|---|
| `ascii` | wandelt Nicht-ASCII in Literalen in `("Pr" & ChrW(252) & "fung")` um. Lokale `Const` mit Umlauten werden zu `Dim` + Zuweisung, Kommentare werden transkribiert, optional Formularbeschriftungen zur Laufzeit gesetzt | idempotent; Prüfmodus `--pruefen` ändert nichts |
| `lint-vba` | ASCII, `Attribute VB_Name` in Zeile 1, Kopfkommentar (Text aus Rechner- oder Projektprofil), `Option Explicit`, eindeutige Fehlernummernkreise je Modul, doppelte öffentliche Namen über Module, Kollision Modul/Prozedur, lokale Variable gleich Hilfsfunktion (L005), Farbwerte nur im Design-Modul, verbotene Konstrukte je Profil (`#If Mac`, `Exp`, Excel-Konstanten ohne lokale `Const`, Formelfunktionen nach Excel 2016) | Befunde mit Regel-ID `OB-Lxxx` |
| `lint-sql` | Access-SQL-Dialekt (kein `CASE`, `LIMIT`, `COUNT(DISTINCT)`), Ladereihenfolge, Namensschema `q/p/a/x/erg_/sys_` | dto. |
| `datenschutz` | Muster (IBAN, USt-IdNr., E-Mail außer erlaubten, Projektmuster für Aktenzeichen) und Namensabgleich gegen eine **Namensquelle**, die ein Projektbefehl liefert. Die Namen bleiben nur im Speicher, Fachwortliste und Stoppwörter kommen aus dem Projekt | nur Zähler und Maske `Ab****` (über `auditcore_privacy`), Exit 1 bei Treffern |
| `mcp` | Nutzlast aus der **vollständigen aktiven Modulmenge**, Sitzungsweg (`vba_session_open/add_module/status/check/close`) mit `expected_sha256` und Manifest-Hash, sonst ein Projektaufruf. Paginierung vollständig, Retry mit Backoff bei `max_concurrent`, Teilmengen je Eigentümer, wenn das Zeitlimit droht, optional `vba_kompilieren` mit Typvertrag und `access_check_sql/schema/ui` mit Manifest | Nachweis `pruefung/letztes-gate.json` |

```python
def mcp_gate(
    mods: ModuleSet,
    host: Host,
    endpoint: Endpoint,
    *,
    subsets: SubsetPolicy,
    contract: Path | None,
    accepted: Sequence[AcceptedWarning],
) -> GateEvidence: ...
def manifest_sha256(mods: ModuleSet) -> str: ...  # sortiert, "<datei>:<sha256>\n", LF-normalisiert
def finding_hash(finding: Mapping[str, object]) -> str: ...  # für begründete Warnungen
```

**CLI:** `gate ascii <dateien>`, `gate lint [--junit {ausgabe}]`,
`gate datenschutz [--junit …]`, `gate mcp --ziel intern|oeffentlich
[--teilmengen eigentuemer]`, `gate alle` (Reihenfolge ascii → lint →
datenschutz → mcp, Abbruch beim ersten Rot).

**Festlegungen:**

- An den MCP geht nur Code, der Lint und Datenschutz-Gate mit 0 bestanden hat.
- **Zeitlimit:** Der Server bricht bei vielen Modulen (ab etwa 21) nach 300 s
  ab, über Cloudflare kommt bei langen Läufen 524. Daher gibt es
  Endpunktprofile: öffentlich (OAuth/Token) oder intern (per SSH-Tunnel auf
  dem Server). Zusätzlich lassen sich Teilmengen je Eigentümer mit den
  nötigen Hilfsmodulen bilden. Scheinbefunde für Bezeichner außerhalb der
  Teilmenge (S008/S009/F009) werden als `teilprojekt` markiert und **nicht**
  ausgeblendet, bis der MCP `scope_modules` anbietet.
- `quality_gate = INCOMPLETE` wegen später Bindung ist normal und kein Fehler.
  `errors = 0` ist das Kriterium. Jede `warning` braucht eine Begründung in
  `pruefung/mcp_warnungen_<kuerzel>.md` (Finding-Hash, Grund).
- Befundtexte sind Daten. Die CLI gibt sie gekürzt und maskiert aus und führt
  nichts aus, was darin steht.
- Der Token kommt aus Umgebung oder Schlüsselbund, nie aus Argumenten, und wird
  nie ausgegeben.

### 2.9 `delivery` – Lieferpaket ohne Daten

```python
@dataclass(frozen=True)
class PackageSpec:
    name: str
    version: str
    date: str  # → JJJJMMTT_<Name>_<Version>
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    layout: Mapping[str, str]


def build_package(spec: PackageSpec, out: Path) -> PackageResult: ...  # deterministisches ZIP
def verify_package(
    zip_path: Path,
) -> list[Finding]: ...  # Hashes, verbotene Endungen, Datenschutz-Gate
def redact_protocol(text: str, rules: RedactionRules) -> str: ...  # Beträge kürzen, Nummern → [Nr.]
def upload(folder: Path, remote: RemoteRef) -> UploadReport: ...  # rclone copy + check --one-way
```

**CLI:** `liefern paket`, `liefern pruefen <zip>`,
`liefern schwaerzen <protokoll>`, `liefern hochladen --ziel <profilname>`.

**Festlegungen:**

- Struktur des Pakets (Muster P-PROT): `LIESMICH.md` mit Importanleitung,
  `CHANGELOG_<Version>.md`, `src/` (UTF-8/LF, Bearbeitungsfassung), `Module/`
  (CP1252/CRLF, Importfassung), `Pruefung/` (Gate-Nachweise, Lauf-Protokolle,
  Werkzeugkopien), `PAKET_SHA256.json` (Datei → Hash, Paket-Hash, Erzeuger,
  Commit). Dateinamen folgen dem Muster `JJJJMMTT_NAME_Version`.
- **Datenfreiheit wird geprüft, nicht angenommen.** Verbotene Endungen und
  Ordner (`daten/`, `ergebnisse/`, Ergebnis-xlsx, Merkmals-CSV), das
  Datenschutz-Gate über alle Textdateien sowie die Schwärzung von
  Abnahmeprotokollen (Ist/Soll-Beträge abschneiden, Vorgangsnummern →
  `[Nr.]`, Warnzeilen entfernen) mit anschließender grep-Gegenprobe.
- **Upload** nur mit bestandenem `liefern pruefen`. Das Ziel (rclone-Remote,
  Ordner-ID) steht im Rechnerprofil unter einem Namen. Danach läuft
  `rclone check --one-way`, Abweichungen machen den Upload rot.

---

## 3 Runner-Profile

Die officebank liefert eine Vorlage für `.auditcore-runner.toml`
(`auditcore-officebank runner-profil --schreiben`). Alle Gates sind eigene
Werkzeuge mit JUnit-Ausgabe. Native Läufe stehen nur im Profil `nativ`, damit
ein fehlender VM-Rechner das Push-Gate nicht rot färbt („nichts geprüft ist
rot“).

| Profil | Auslöser | Werkzeuge | Zweck |
|---|---|---|---|
| `vba` | lokal, Agentenetappe | `ob-ascii` (Prüfmodus), `ob-lint-vba`, `ob-datenschutz`, gitleaks | jede VBA-Änderung, schnell, ohne Netz |
| `access` | lokal | `vba` + `ob-lint-sql`, `ob-abfragen-reihenfolge`, `ob-manifest-statisch` | Access-Projekte |
| `office` | lokal, pr (pre-push) | `access` bzw. `vba` + pytest der Projektwerkzeuge (Sollwerte, Abnahme), `ob-mcp` (optional `aktiv = false` ohne Netz), `ob-paket-pruefen` | vor Commit/Push |
| `nativ` | nur lokal, nur mit VM | `ob-build` (Vollaufbau), `ob-abnahme` | Freigabe einer Fassung |

```toml
[pruefprofile.vba.werkzeug.ob-lint-vba]
befehl = ["auditcore-officebank", "gate", "lint", "--junit", "{ausgabe}"]
zeitlimit_s = 120
prioritaet = 2
```

---

## 4 Plugin `auditcore-office`

### 4.1 Aufbau

```text
plugins/auditcore-office/
  .claude-plugin/plugin.json
  skills/<name>/SKILL.md            Abläufe (Slash-Befehle)
  agents/<rolle>.md                 Agenten-Definitionen
  hooks/hooks.json + hooks/*.py     Schutz- und Prüf-Hooks
  vorlagen/                         Projektvorlagen (Kap. 4.5)
```

Dazu kommt eine Marketplace-Datei `.claude-plugin/marketplace.json` im
auditcore-Root, Installation über `/plugin marketplace add <repo>`, dann
`/plugin install auditcore-office`. Die Skills setzen eine installierte CLI
voraus und prüfen sie zuerst (`auditcore-officebank --version`).

### 4.2 Skills

| Skill | Ablauf |
|---|---|
| `/office-projekt-start` | Bestandsaufnahme → Plan mit Entscheidungsliste (Vorlage) → nach Freigabe Projektgerüst: `.officebank.toml`, `src/`, `werkzeuge/`, `analyse/`, `pruefung/`, `SCHNITTSTELLEN.md`, `MODULLISTE.md`, `AGENTENREGELN.md`, `.gitignore` für Daten, Runner-Profil |
| `/office-vm-einrichten` | Checkliste VM anlegen, OOBE, Gastwerkzeuge, ODT-Installation, Testordner, Vertrauensorte, MTU, Freigabe; jeder Schritt mit Prüfbefehl; manuelle Schritte (Lizenzanmeldung) als Rückfrage an den Nutzer |
| `/office-vm-lauf` | Sperre nehmen → `gate alle` → `build lauf` (aus HEAD) → Abholung → `abnahme pruefen` → Bericht → Sperre freigeben (auch bei Fehler); fasst Laufzeiten und Dialogprotokoll zusammen |
| `/mcp-vorlauf` | `gate ascii/lint/datenschutz` → MCP mit vollständiger Modulmenge (Sitzung oder Teilmengen) → `error` beheben und wiederholen → `warning` je einzeln begründen → Nachweis; meldet `native_office_compile = not_run` |
| `/sollwerte-abnahme` | Sollwert-Gerüst im Projekt (Python, unabhängig von Office), Schema-Prüfung, Abnahme, begründete Abweichungen pflegen, Bericht einsetzen |
| `/lieferpaket` | Fassung, CHANGELOG, LIESMICH, Paket bauen, prüfen, Protokolle schwärzen, nach Rückfrage hochladen, `rclone check` |
| `/qchess-dienst` | Dienst schreiben/starten/prüfen, Restore, App-Login, Client-Konfiguration nach Projektprofil, Positivlisten-Export; nie Secrets anzeigen |
| `/office-mac-probelauf` | Testkopie mit Ersatzklassen, Import per UI-Skripting, kompilieren, Makro mit Dialogbeobachtung; Vorprüfung der Mac-Fallen |

### 4.3 Agenten-Definitionen

| Agent | Rolle | darf | darf nicht |
|---|---|---|---|
| `office-integration` | Fundament, Schnittstellen, Modulliste, Build, **einziger VM-Nutzer** | gemeinsame Module, `SCHNITTSTELLEN.md`, `MODULLISTE.md`, Build-Skripte, VM | fremde Fachmodule ändern (nur über Anträge) |
| `office-fach` (Vorlage mit Kürzel) | Fachmodule und Abfragen eines Bereichs | eigene `src/`-Dateien laut Modulliste, `analyse/antraege_<kuerzel>.md` | VM, Excel/Access-Automation, gemeinsame Module, Vertrag |
| `office-sollwerte` | unabhängige Python-Referenz aus Rohdaten | `werkzeuge/abnahme/`, `sollwerte.json` | Office, VBA, Ergebnisse der Office-Läufe als Quelle |
| `office-mcp-vorlauf` | statische Prüfung, Befunde zuordnen | Nachweise, Warnungsbegründungen, Befundliste je Eigentümer | Code ändern (meldet an Eigentümer) |
| `office-texte` | Anleitung, LIESMICH, CHANGELOG, Methodiktexte | `dokumentation/`, `src/texte/` | Daten, Zahlen aus Ergebnissen ohne Freigabe |
| `office-namensabgleich` | Abgleich der Namen Vertrag ↔ Code ↔ SQL ↔ Sollwerte ↔ Berichtsdefinitionen (Tabellen, Felder, Einstiege) | nur lesen, Bericht `analyse/antraege_Namensabgleich.md` | Dateien anderer ändern |

**Feste Regeln (in jeder Definition):**

1. Nur eigene Dateien schreiben und **nur eigene Pfade stagen**
   (`git add <pfade>`). `git commit -a`, `git add -A/.` und `git reset --hard`
   sind verboten (Hook, Kap. 4.4). Fremde Änderungen werden nicht
   zurückgesetzt, sondern gemeldet.
2. Änderungswünsche an gemeinsame Module oder den Vertrag gehen als **Antrag**
   (Signatur, Begründung) an den Integrations-Agenten. Bis dahin gilt eine
   private Hilfsroutine mit Präfix.
3. Die VM nutzt nur der Integrations-Agent, und nur mit Sperre. Gesamtläufe
   werden gebündelt.
4. Datenschutz: keine Namen, Freitexte, Beträge oder Kennungen aus echten
   Daten in Code, Kommentaren, Tests, Commits, Logs oder Antworten. Nichts geht
   an externe Dienste ohne bestandenes Datenschutz-Gate.
5. Nie „kompiliert“ oder „getestet“ behaupten ohne nativen Nachweis (Protokoll
   mit `IsCompiled`, Lauf-ID). Statisch heißt `native_office_compile = not_run`.
6. Nach `error` korrigieren und erneut prüfen. Nach zwei erfolglosen Versuchen
   ohne gefundene Ursache anhalten und berichten.
7. Antwort an den Koordinator in höchstens 20 Zeilen: Commit, Dateien, Zähler
   (Lint, Datenschutz, MCP), Anträge, offene Punkte.
8. **Beim Agentenende** trägt der Integrations-Agent verwaiste Module in der
   Modulliste ausdrücklich neu ein (Eigentümer „Integration (übernommen
   <Datum>)“).

### 4.4 Hooks

| Hook | Ereignis | Wirkung |
|---|---|---|
| `kein-sammelcommit` | PreToolUse (Bash) | blockiert `git commit -a`, `git add -A`, `git add .` und `git reset --hard` in Office-Projekten |
| `vba-geaendert` | PostToolUse (Write/Edit auf `*.bas`, `*.cls`, `*.frm`) | führt `gate ascii --pruefen` und `gate lint` für die Datei aus und erinnert an den MCP-Vorlauf (globale Arbeitsregel) |
| `vm-sperre` | PreToolUse (Bash mit `auditcore-officebank vm nutzer\|build lauf`) | verweigert ohne eigene Sperre |
| `keine-secrets` | PostToolUse (Bash) | maskiert Ausgaben mit Token-, Passwort- oder Verbindungszeichenfolgen-Mustern und warnt (nach der Passwortanzeige vom 05.10.) |

### 4.5 Vorlagen

- `SCHNITTSTELLEN.md`: Ablage, Namenskonvention, Datenmodell, Quellkopien,
  System-/Ergebnistabellen, Fehlernummernkreise, verbindliche Signaturen,
  Fassungszeilen.
- `MODULLISTE.md`: Modul, Eigentümer, Etappe, im Build ja/nein,
  Build-Reihenfolge, Gesamtlauf mit Einstiegen (`Public Function …() As String`
  ohne Pflichtargument, fängt eigene Fehler ab), Prüfkette.
- `Plan_<Projekt>_0.1.md`: Kurzfassung, Bestandsaufnahme, Zielarchitektur,
  Abnahme, Etappen mit AT, Abnahmekriterien, Risiken, **Entscheidungsliste**
  (E-Nummer, Optionen, Empfehlung, Markierung `[MUSS vor X]`) und am Ende
  „Nutzerentscheidungen vom <Datum>“ (verbindlich).
- `AGENTENREGELN.md`: Pflichtlektüre, Quelltextregeln, Datenschutz,
  Prüfkette, Git-Regeln, Antwortformat, Abschnitt für Entscheidungen während
  der Etappe.
- `antraege_<kuerzel>.md`, `mcp_warnungen_<kuerzel>.md`, Abnahmebericht mit
  AUTO-Marken, `LIESMICH.md`/`CHANGELOG_<Version>.md` des Lieferpakets.
- Best-Practice-Leitfaden Access/VBA (BP1–BP17 aus P-ACC, ohne Projektbezug)
  als Nachschlagewerk für den Fach-Agenten.

---

## 5 Lehren vom 05.10.2026 als Anforderungen

Jede Falle wird zu einer Prüfung, einer Vorgabe im Gastskript oder einem
Hinweis. Spalte „Umsetzung“ nennt den Ort.

| Nr | Falle | Umsetzung |
|---|---|---|
| L01 | Mac-Excel speichert VBA im Mac-Zeichensatz, Windows liest CP1252 → Laufzeitfehler 9 bei Umlauten | `gate ascii` Pflicht, `lint-vba` ASCII-Regel, Import nur CP1252/CRLF |
| L02 | Excel liest `NumberFormat` von Diagrammen landesspezifisch („#.##0“), auf dem Mac ab dem 2. Setzen falsch gespeichert | Formatroutinen-Vorlage, Kontrolle über Chart-XML |
| L03 | `FormatConditions`-Formeln erwarten UI-Sprache → Fehler 5 | Hinweisregel, Vorlage `FormelBedingung` |
| L04 | Mac: kein `Scripting.Dictionary`, kein `CDec`, kein VBProject-Zugriff per Makro, Sandbox je Ordner, Bildschirmsperre, Entwurfsmodus | `excel_mac.preflight()`, Testkopie mit Ersatzklasse, Lint-Profil `mac` |
| L05 | `DSum/DLookup/DCount` sehen offene DAO-Transaktionen nicht → 0/Null | Lint-Hinweis, Leitfaden, Abnahme deckt es auf; MCP-Regel beantragt |
| L06 | `CurrentDb.TableDefs(…).Fields` → 3420; `CreateProperty` ohne Setzversuch → 3367 | Vorlagenroutinen im Modell-Modul, Leitfaden |
| L07 | Abfragen in falscher Reihenfolge geladen | `access.query_load_order()` |
| L08 | Word `Content.Text` ohne Listennummern | Vorlage `WordDokumentText` mit `ListFormat.ListString` |
| L09 | Eigene Word-Instanz bleibt stehen | Gastskript prüft `WINWORD.EXE` vorher/nachher, Vorlage „eigene Instanz beenden“ |
| L10 | Office-COM als SYSTEM ohne Lizenz | `UserSession` (Aufgabenplanung, Interactive) |
| L11 | Modale Dialoge halten COM an; VBA-Laufzeitfehlerdialog (Knopf 4800), NUIDialog nach Makroende | Dialogwächter mit JSON-Regeln, Regel `vba-laufzeitfehler` → Foto, Text protokollieren, „Beenden“; Einstiege fangen eigene Fehler ab |
| L12 | UTM-Tastatur per AppleScript verfälscht Zeichen; Host-Screenshot eingefroren | Scancodes je Layout, Fotos im Gast |
| L13 | MCP: 300 s Zeitlimit ab ~21 Modulen, 524 über Cloudflare, `max_concurrent = 2`, Scheinfehler bei Teilmengen | Endpunktprofile, Teilmengen, Retry/Backoff, Markierung `teilprojekt` |
| L14 | Module bleiben nach Agentenende verwaist | Regel 8, `project.ownership` meldet Module ohne aktiven Eigentümer |
| L15 | Versehentliches `git commit -a` übernimmt fremde Arbeitsstände | Hook `kein-sammelcommit`, Build nur aus Commits |
| L16 | UTM-ISO-Lesezeichen zeigen nach dem Verschieben ins Leere | `vm pruefen`: ISO-Pfade prüfen, ISOs in festem Ordner |
| L17 | PowerShell: `if`-Ausdruck entpackt 1-Element-Arrays; `''` in Bash-Einzelquotes zerstört PS-Strings; Umlaute inline verfälscht | Gastskripte nur als Dateien (UTF-8 mit BOM), Parameter per JSON-Datei, `@(...)` erzwingen |
| L18 | `Compress-Archive` schreibt `\` als Trenner | `ZipFile`-API, SHA-256 beidseitig |
| L19 | `Access.Run` mit Argument braucht `[ref]`; DAO/ACE direkt aus PowerShell hängt | Schrittsprache kapselt es |
| L20 | Access-Schaltflächen unsichtbar für UIA | Klickprobe über OnClick-Ausdrücke, Koordinatenklick über `OFormSub` |
| L21 | openpyxl zerstört Formulare in xlsm | Schreiben nur über Objektmodell, Lint der Projektwerkzeuge |
| L22 | Secrets in Agentenausgabe (Passwortrotation nötig) | Maskierung aller CLI-Ausgaben, Hook `keine-secrets` |
| L23 | Mehr Kerne beschleunigen Access/VBA nicht | Inkrementeller Build, Laufzeitprotokoll, PDF nur geändert |
| L24 | `IIf` wertet beide Zweige aus; `Empty` ≠ `Null`; Bedingung unter `On Error Resume Next` springt in den Then-Zweig | Lint-Hinweise (bis MCP-Regeln da sind) |
| L25 | Excel `SaveAs` 1004 bei gleichnamiger offener Mappe; Log-Achse ≤ 0 öffnet modalen Dialog | Lint-Hinweise, Dialogregel |
| L26 | QChess-Client: `Server=` statt `Data Source=`, fester Temp-Ordner, Lokalmodus überschrieben, Login = Windows-Benutzer | Prüfpunkte im Projektprofil, `mssql client-konfig` |
| L27 | Container-Port-Bindung an VPN-Adresse scheitert, wenn Docker vor dem VPN startet | `mssql pruefen` |
| L28 | Docker Desktop und VM zusammen auf 16-GB-Rechnern → Swap | `vm pruefen` |
| L29 | Öffentliche/mobile Uplinks mit Path-MTU 1280 → Abbrüche | `vm pruefen`, Gast-MTU-Empfehlung |

---

## 6 Sicherheit, Datenschutz, Tests, Release

### 6.1 Sicherheit und Datenschutz

- **Keine Daten im Paket:** Paketdaten nur Skripte, Schemas, Vorlagen.
  Ein Test prüft das Wheel auf verbotene Endungen (`.mdb`, `.accdb`, `.xlsx`,
  `.xlsm`, `.docx`, `.bak`, `.csv` außer Fixtures-Allowlist) und auf
  Zeichenketten, die wie Adressen, Ordner-IDs oder E-Mails aussehen.
- **Tests nur synthetisch:** Fixtures sind erfundene Mini-Datenbestände
  (Hypothesis, kleine CSV), keine Kopien echter Berichte.
- **Secrets** nur aus Umgebung, `.env` (600) oder macOS-Schlüsselbund
  (`security find-generic-password`). Referenzen in der Konfiguration sind
  Namen (`SecretRef("flowaudit-mcp")`), nie Werte. Keine Secrets in
  Argumentlisten (sichtbar in `ps`).
- **Maskierung:** Ein zentraler Ausgabefilter maskiert Bearer-Token,
  `Password=`/`Pwd=`/`SA_PASSWORD`, Verbindungszeichenfolgen und Muster aus der
  Projektkonfiguration, bevor etwas auf stdout, in Protokolle oder Nachweise
  gelangt.
- **Austauschserver:** bindet nur an das VM-Hostnetz, mit Token, ohne
  Verzeichnisliste, mit Größenlimit je Datei, und wird nach dem Lauf geleert.
- **Gastrechte:** `AccessVBOM` und Vertrauensorte nur für Testordner; kein
  Abschalten der Makrosicherheit.
- **Upload** nur nach `liefern pruefen`. Ergebnisse mit Klarnamen bleiben in
  `ergebnisse/` (gitignored, nie hochgeladen).

### 6.2 Tests

- **Ohne Office (CI, Pflicht):** Unit-Tests für Konfiguration, Scancodes,
  ASCII-Umwandlung (Eigenschaft: der erzeugte VBA-Ausdruck ergibt mit einem
  kleinen Auswerter wieder den Originaltext), Lint-Regeln (je Regel positiv
  und negativ), Datenschutz-Gate, Manifest-Hash, MCP-Client gegen einen
  Fake-Server (Sitzung, Paginierung, 300-s-Abbruch, `max_concurrent`),
  Build-Plan (Inkrement, Abhängigkeiten), Abnahme (Toleranzen, deutsche Zahlen,
  begründete Abweichungen), Paketbau (deterministisches ZIP mit
  `SOURCE_DATE_EPOCH`), Schwärzung, Gastskript-Erzeugung als Golden Files,
  `FakeGuest` und `FakeSession` mit aufgezeichneten Ausgaben.
- **Gastskripte:** ASCII-Prüfung, Parse-Test mit `pwsh -NoProfile -Command
  { [ScriptBlock]::Create(...) }`, sofern pwsh vorhanden (Marker
  `pwsh`), optional PSScriptAnalyzer.
- **Mit Office (optional, nie in CI):** Marker `vm` und `office_mac`. Ein
  Integrationstest baut ein synthetisches Mini-Projekt (zwei Module, eine
  Abfrage, ein Bericht, ein Excel-Makro, ein Word-Dokument), führt es in der VM
  aus und prüft `IsCompiled`, Zähler, Fotos und dass kein WINWORD.EXE übrig
  bleibt. Das Ergebnis wird als Nachweis-JSON abgelegt, nicht als Testbehauptung.
- Paketregeln: `tests/test_architecture.py` (keine Plattform-Werkzeuge
  importieren), `auditcore-codegate check`, Ratchet, `mypy --strict`.

### 6.3 Release und Versionierung

- Neues Paket `packages/auditcore_officebank` 0.1.0, `provenance.json` mit
  `NEW_IMPLEMENTATION`. Die Quellen sind private Projektskripte und werden nur
  allgemein beschrieben („aus Projektwerkzeugen neu geschrieben“), ohne Pfade.
  README nach `docs/bibliotheken/readme-vorlage.md`, Katalog per
  `scripts/docs/catalog.py --write`, CHANGELOG-Eintrag.
- Veröffentlichung im nächsten Pre-release mit öffentlichem
  Installationsnachweis (`docs/reports/domain-public-installation-v<…>.json`),
  wie bei den übrigen Paketen.
- Das Plugin hat eine eigene Version in `plugin.json`, gekoppelt an die
  Mindestversion der CLI (`requires auditcore_officebank>=0.1.0`, Prüfung im
  Skill). Ein Plugin-Release erfolgt mit demselben Repo-Tag.
- Schemas (Projektdatei, Sollwerte, Gate-Nachweis, Paket-Manifest) tragen
  Versionen (`auditcore-officebank/projekt/1` …) mit Migration wie beim
  Runner-Profil.
- Gastskripte tragen eine Version und einen Hash. Der Lauf protokolliert, welche
  Fassung im Gast lief.

---

## 7 Etappen und Entscheidungen

### 7.1 Etappen

| Etappe | Inhalt | Ergebnis | AT |
|---|---|---|---:|
| **0 Gerüst** | Paket, Konfiguration (Rechnerprofil, Projektdatei, Schemas), CLI-Rahmen, Ausgabe-Maskierung, Fakes, Spezifikation | leeres, geprüftes Paket | 1,5 |
| **1 Gates** | ascii, lint-vba, lint-sql, datenschutz, MCP-Client mit Sitzung/Teilmengen/Retry, Nachweis, JUnit | `gate alle` ersetzt die Projektskripte | 3 |
| **2 VM** | UTM-Backend, Austauschserver mit Token, Benutzersitzung, Sperre, Fotos, Scancodes, Dialogwächter, Einrichtung inkl. ODT, `vm pruefen` | `vm nutzer` stabil, Golden-File-Tests | 3 |
| **3 Office** | Excel (Windows + Mac-UI), Access (Bau, Abfragen, Schrittsprache, Manifest-Export, Komprimieren), Word (Prozesskontrolle, Design, Vorlage ListFormat) | Mini-Projekt läuft nativ | 4 |
| **4 Build, Abnahme, Lieferung** | inkrementeller Build, ZIP-Abholung, Laufzeiten; Abnahme mit Toleranzen und Bericht; Paketbau, Schwärzung, Upload | Ende-zu-Ende ohne Projektskripte | 3 |
| **5 SQL-Server-Dienst** | compose, Restore, Login, Client-Konfig nach Profil, Positivlisten-Export | QChess-Testdienst reproduzierbar | 1,5 |
| **6 Runner, Plugin, CI-Vorlage** | Runner-Profilvorlage, Plugin mit 8 Skills, 6 Agenten, 4 Hooks, Vorlagen, Marketplace; wiederverwendbarer Workflow `officebank-statisch` (Kap. 8.6) | `/office-vm-lauf` durchgängig, CI-Vorlage grün an einem Testprojekt | 3,5 |
| **7 Pilot P-ACC + Release** | P-ACC nach Kap. 8.2 umstellen, Vollaufbau und Abnahme wie vorher, Abweichungen beheben, Release 0.1.0 mit Installationsnachweis | Fassung 0.1.0 | 2,5 |
| **8 Migration P-XL1, P-XL2, P-PROT** | nach Kap. 8.3–8.5, je Projekt Gleichstandsnachweis (gleiche Importdateien, gleiches Gate-Ergebnis, gleiche Abnahme) und CI-Workflow | alle vier Projekte auf 0.1.x | 3 |
| **Summe** | | | **25** |

Abhängigkeiten: 1 und 2 parallel nach 0; 3 braucht 2; 4 braucht 1 und 3; 5
unabhängig nach 0; 6 braucht 1–4; 7 vor 8; in 8 laufen die drei Projekte
parallel (je ein Agent, VM nur über den Integrations-Agenten). Mit zwei bis drei
Agenten parallel sind etwa 15–16 Kalendertage realistisch.

### 7.2 Offene Entscheidungen

**E01 Freigabe des Plans** [MUSS vor 0]
- Optionen: (a) wie vorgelegt; (b) zuerst nur Gates + Plugin (Etappen 0, 1, 6
  ohne VM, rund 7 AT); (c) mit Änderungen.
- Empfehlung: (a). Der größte Zeitgewinn steckt in VM, Build und Abnahme.

**E02 Paketname und -schnitt** [MUSS vor 0]
- Optionen: (a) ein Paket `auditcore_officebank` mit Extras `[docx]`
  (python-docx), `[xlsx]` (openpyxl, nur lesend); (b) zwei Pakete
  `auditcore_vm` + `auditcore_office`; (c) drei Pakete (vm, office, gates).
- Empfehlung: (a). Die Teile werden immer zusammen benutzt, und der Kern bleibt
  ohne Abhängigkeiten. Ein Schnitt ist später ohne API-Bruch möglich, weil die
  Unterpakete getrennt sind.

**E03 Ort des Plugins** [MUSS vor 6]
- Optionen: (a) im auditcore-Monorepo unter `plugins/auditcore-office/` mit
  `marketplace.json` im Root; (b) eigenes öffentliches Repo; (c) nur lokal
  unter `~/.claude/`.
- Empfehlung: (a). Plugin und CLI werden gemeinsam versioniert und getestet,
  und die Skills können in der CI auf gültige CLI-Befehle geprüft werden.

**E04 Lizenz** [MUSS vor 7]
- Optionen: (a) MIT wie die übrigen Pakete (inkl. Gastskripte und Vorlagen);
  (b) Apache-2.0.
- Empfehlung: (a). Office, ODT-`setup.exe` und SQL-Server-Image werden nicht
  mitgeliefert, sondern zur Laufzeit vom Hersteller geladen. Der Kopfkommentar
  des Autors in VBA-Vorlagen ist Konfiguration, nicht Paketinhalt.

**E05 QChess im öffentlichen Paket** [MUSS vor 5]
- Optionen: (a) generischer `mssql`-Dienst öffentlich, QChess-Client nur als
  privates Projektprofil (Konfigurationsschlüssel, Prüfpunkte); (b) eigenes
  Modul `qchess` öffentlich; (c) alles privat.
- Empfehlung: (a). Ein Teil des QChess-Wissens stammt aus der Analyse des
  Herstellerprogramms und darf nur als Clean-Room-Beschreibung verwendet
  werden. Im öffentlichen Paket stehen deshalb nur beobachtbare
  Konfigurationsprüfungen, die das Profil liefert.

**E06 Plattformen** [vor 2]
- Optionen: (a) Host macOS + UTM zuerst, Backend-Schnittstelle für
  libvirt/QEMU (Linux) vorbereitet, Gast Windows 11 ARM/x64 mit Office 365
  64 Bit; (b) zusätzlich gleich Hyper-V/Windows-Host; (c) nur macOS.
- Empfehlung: (a). Der Gastagent ist QEMU-Standard, ein libvirt-Backend ist
  später klein.

**E07 Datenweg Gast ↔ Host** [vor 2]
- Optionen: (a) HTTP-Austauschserver mit Token als Standard, SPICE-WebDAV
  optional; (b) WebDAV als Standard.
- Empfehlung: (a). Er ist skriptbar ohne UI-Einrichtung und hat sich am
  05.10. bewährt. Für große Ergebnisse gibt es ein ZIP mit SHA-256.

**E08 Bezeichner und CLI-Sprache** [vor 0]
- Optionen: (a) Python-API englisch (AGENTS.md), CLI und Meldungen deutsch
  wie beim Runner; (b) alles deutsch.
- Empfehlung: (a).

**E09 Format der begründeten Abweichungen** [vor 4]
- Optionen: (a) TOML (stdlib `tomllib`, keine Abhängigkeit) mit Lesepfad für
  das bisherige YAML über Extra; (b) YAML beibehalten.
- Empfehlung: (a).

**E10 MCP-Client** [vor 1]
- Optionen: (a) eigener Streamable-HTTP-Client mit Standardbibliothek (wie
  heute, rund 150 Zeilen); (b) offizielles `mcp`-SDK als Extra.
- Empfehlung: (a), mit Fake-Server-Tests. Das SDK bringt viele Abhängigkeiten
  für drei Aufrufe.

**E11 Mehrbenutzer-Sperre** [vor 2]
- Optionen: (a) Sperrdatei mit TTL in 0.1, Adapter zu `auditcore_flow_agent`
  später; (b) gleich über `auditcore_flow_agent`.
- Empfehlung: (a).

**E12 Reihenfolge der Migration** [vor 7]
- Optionen: (a) P-ACC als Pilot (Access, Word, Build, Abnahme,
  MCP-Teilmengen, also die größte Abdeckung), danach P-XL1, P-XL2 und P-PROT
  parallel; (b) P-XL1 zuerst (kleinster Umfang); (c) alle vier gleichzeitig.
- Empfehlung: (a). Was am Piloten bricht, wird einmal in 0.1.x behoben statt
  viermal.

**E14 Datenschutz-Gate in der CI** [vor 6]
- Ausgangslage: Die Namensquellen (Beleg-Datenbank, Berichte) liegen nie im
  Repo und nie auf GitHub. Der Namensabgleich kann deshalb nur lokal laufen.
- Optionen: (a) CI prüft nur Muster und den **lokalen Gate-Nachweis**
  (Manifest-Hash des Nachweises = Manifest des geprüften Commits, Treffer = 0).
  Der Nachweis entsteht im Pre-push-Hook; (b) zusätzlich eine Liste
  verschlüsselter Namens-Hashes (HMAC, Schlüssel als Secret) im Repo;
  (c) nur Muster.
- Empfehlung: (a). (b) legte pseudonymisierte Personendaten ins Repo, (c)
  ließe den Namensabgleich unbelegt.

**E15 Form der CI-Vorlage** [vor 6]
- Optionen: (a) wiederverwendbarer Workflow im öffentlichen auditcore-Repo,
  aus den privaten Repos per Commit-SHA aufgerufen; (b) Workflow-Datei als
  Vorlage, per `projekt start` ins Projekt kopiert; (c) Composite Action.
- Empfehlung: (a). Die Logik wird einmal gepflegt, die Projekte pinnen nur
  den SHA (Renovate hebt ihn an). Projektwerte kommen als `inputs`, das Token als
  `secrets`.

**E16 Repository für P-PROT** [vor 8]
- Ausgangslage: P-PROT liegt bisher in Fassungsordnern ohne Git.
- Optionen: (a) neues privates Repo aus der letzten Fassung (nur `src/`,
  Werkzeuge, Doku, Prüfnachweise ohne Daten), ältere Fassungen als Tags
  nachgezogen; (b) weiter ohne Git, nur lokale Gates.
- Empfehlung: (a). Ohne Repo gibt es weder Build aus Commits noch CI.

**E13 Ablage dieses Plans**
- Der Auftrag nannte `docs/plaene/`. Diesen Ordner gibt es im Repo nicht, und
  laut `docs/README.md` gehören Projektpläne nach `docs/projekt/`. Deshalb liegt
  der Plan dort.
- Empfehlung: dort belassen. Alternative: `docs/plaene/` anlegen und in
  `docs/README.md` eintragen.

---

## 8 Migration der ersten Nutzer

Die vier Pilotprojekte sind die ersten Nutzer. P-ACC, P-XL1 und P-XL2 liegen
in eigenen privaten Repositories, P-PROT bekommt eines (E16). Welches private
Repo zu welchem Kürzel gehört, steht nur in den Projekt-Repos selbst (Datei
`MIGRATION_officebank.md`), nicht hier.

### 8.1 Gemeinsames Vorgehen je Projekt

1. **Bestand einfrieren:** Tag `vor-officebank`, letzte Gate-Nachweise und
   Abnahme als Referenz sichern.
2. **`.officebank.toml` anlegen** (Schema `auditcore-officebank/projekt/1`):
   Host, Quellordner, Modulliste mit Reihenfolge und Eigentümern (oder Verweis
   auf `MODULLISTE.md`), Lint-Profil, Kopfkommentar, Fehlerkreise,
   Namensquellen-Befehl für das Datenschutz-Gate, Fachwort- und Stoppwortlisten,
   Gast-Testordner, Schritte, Dialogregeln, Paketlayout, Schwärzungsregeln,
   Upload-Ziel als **Name** (die Ordner-ID steht im Rechnerprofil).
3. **Werkzeuge ersetzen** (Tabellen unten). Ersetzte Skripte werden gelöscht,
   nicht auskommentiert. Projektspezifische Prüfungen bleiben als kleine Module
   in `werkzeuge/` und nutzen die Bibliothek.
4. **Gleichstandsnachweis:** gleiche Importdateien (byteweise, CP1252/CRLF),
   gleiches MCP-Ergebnis (Zähler je Schwere, Manifest-Hash), gleiche Abnahme
   (alle Prüfungen, gleiche begründete Abweichungen) wie beim Tag
   `vor-officebank`. Abweichungen werden erklärt oder in der Bibliothek
   behoben.
5. **Runner-Profil** `.auditcore-runner.toml` aus der Vorlage, Baseline
   anlegen, Pre-push-Hook (`auditcore-runner hook --schreiben`).
6. **CI-Workflow** `.github/workflows/vba-statisch.yml` (Kap. 8.6).
7. **Agentenregeln** auf die Plugin-Agenten umstellen. Projektregeln (Entscheidungen,
   Ausnahmen) bleiben in `AGENTENREGELN.md` des Projekts.

### 8.2 P-ACC (Access + Word, Pilot)

| bisher (Projekt) | künftig |
|---|---|
| `werkzeuge/lint_vba.py` | `gate lint` (Profil `access`; Design-Modul, Fehlerbasis-Muster und Kopfkommentar aus `.officebank.toml`) + `gate lint-sql` |
| `werkzeuge/datenschutz_gate.py` | `gate datenschutz`; Namensquelle als Projektbefehl (Export aus der lokalen Beleg-Datenbank nach stdout), Fachwortliste und Aktenzeichenmuster in der Projektdatei |
| `werkzeuge/mcp_gate.sh`, `mcp_vba_check.py` | `gate mcp --host access --teilmengen eigentuemer` (Teilmengen aus `MODULLISTE.md`), zusätzlich `access_check_sql/schema/ui` mit statischem Manifest |
| Build-Skript und Gast-Laufskript | `build lauf <kennung>` + `office.access` (Schrittsprache), ZIP-Abholung, `SHA256SUMS.txt` |
| `abnahme/abnahme_access.py` (Vergleichskern, Zahlen lesen, Toleranzen), `begruendet.py`, `bericht_aus_abnahme.py` | `abnahme pruefen` / `abnahme bericht`; begründete Abweichungen als TOML (Umwandlung einmalig) |

Bleibt im Projekt: `src/` (VBA, Abfragen, Texte, Stammdaten),
`SCHNITTSTELLEN.md`, `MODULLISTE.md`, `DIAGRAMM_ENTSCHEIDUNG.md`, Plan mit
Nutzerentscheidungen, `sollwerte.py` und `sollwerte*.json`, die fachlichen
Prüfgruppen der Abnahme (als Projekt-Plug-in für `compare`), die
Pseudonym-Übersetzung (als Hook mit lokalem Schlüssel), der
Vorschlag der QChess-Export-View (künftig über `mssql export` mit
Positivliste), Katalogdateien. Statistikfunktionen  werden
mit `auditcore_statistics` abgeglichen. Was dort fehlt, wird als eigene
Paketänderung beantragt und nicht in die officebank kopiert.

Runner: Profile `access` (jede Etappe), `office` (Pre-push, mit pytest der
Sollwert- und Abnahmewerkzeuge auf synthetischen Fixtures), `nativ`
(Vollaufbau + Abnahme, nur Integrations-Agent).

### 8.3 P-XL1 (Excel, Windows-Ziel, Mac-Probelauf)

| bisher (Projekt bzw. Scratchpad) | künftig |
|---|---|
| `werkzeuge/ascii_quelltext.py` | `gate ascii` (inkl. Option Formularbeschriftungen) |
| `werkzeuge/lint.py` (L000–L007), `projekt.py` | `gate lint` (Profil `excel`, Pflichtmodule und Modulanzahl aus der Projektdatei); projektspezifische Regeln als Lint-Erweiterung im Projekt |
| `werkzeuge/build.py` (Nachweisprüfung, CP1252-Import), `mcp_payload.py`, Scratchpad-Skripte für den MCP-Aufruf | `gate mcp` über den Sitzungsweg (wie im Projektdokument `gate.md`), `gates.evidence` (Manifest, akzeptierte Warnungen per Finding-Hash), `office.excel.to_import_files` |
| `werkzeuge/mac_probelauf/testkopie.py` + Ersatzklasse, Scratchpad-AppleScripts für VBE-Import, Kompilieren, Makrolauf | `excel mac-probelauf` (generische Wörterbuch-Ersatzklasse im Paket) |
| Gastskripte für Trägermappe und Makrolauf | `excel traeger --versionszeile …`, `excel lauf --regeln …` |
| Drive-Upload von Hand (rclone, Schwärzung per grep) | `liefern paket/schwaerzen/hochladen` (Regeln: Beträge abschneiden, Vorgangsnummern → `[Nr.]`) |

Bleibt im Projekt: `src/` (Module, Formular-Einbettung), `typvertrag.py`
(Fachaussagen zum Datenmodell, liefert den Vertrag für `vba_kompilieren` im
Format der Bibliothek), die Abnahmeskripte je Fassung (fachliche Prüfungen auf
der Ergebnismappe; sie nutzen künftig `acceptance` für Lesen, Toleranzen und
Bericht), die Random-Forest-Auswertung, `CHANGELOG_*`. Der ToF-Katalog wird
mit `auditcore_tyfindings` abgeglichen, das aus diesem Projekt stammt.

Runner: `vba` (jede Änderung), `office` (Pre-push: `vba` + pytest der
Abnahmewerkzeuge + `ob-mcp`), `nativ` (Trägermappe bauen + Lauf + Abnahme).
Lint-Profil zusätzlich `mac` (Mac-Fallen als Hinweis), weil das Projekt auf
dem Mac kompiliert wird.

### 8.4 P-XL2 (Excel, Windows und Mac)

| bisher (Projekt) | künftig |
|---|---|
| `werkzeuge/ascii_quelltext.py` (Kopie aus P-XL1) | `gate ascii` |
| projekteigener Lint | `gate lint` (Profil `excel2016`: verbotene Formelfunktionen nach Excel 2016, keine CSE-Matrixformeln, keine Literal-Listen in `Validation.Add`, Plattformweiche statt `#If Mac`, lokale Variable gleich Hilfsfunktion) |
| `werkzeuge/datenschutz_gate.py` | `gate datenschutz` mit projektbezogenen Stoppwörtern (öffentliche KOM-Begriffe) und der Stufe „Hinweis“ für erlaubte Fälle aus den Nutzerentscheidungen |
| `werkzeuge/mcp_payload.py`, `mcp_*_ergebnis.json`, `mcp_warnungen_*.md` | `gate mcp --host excel` (inkl. Dokumentmodule und Formular), Nachweise und Warnungsbegründungen im Standardformat unter `pruefung/` |
| drei projekteigene Gastskripte (Lauf, Robustheit, Bewertung) | `excel lauf` mit Schritten (Steuerzellen setzen, Makro ohne Dialoge, Bewertungsblatt) und Dialogregeln aus der Projektdatei |
| Anträge `antraege_*.md` | Vorlage aus dem Plugin, gleiche Ablage |

Bleibt im Projekt: `src/vba/` mit `SCHNITTSTELLEN.md`, das Abnahmeskript
gegen die Referenzmappe (Lokatoren), `make_tyf_katalog.py` (Abgleich mit
`auditcore_tyfindings`), `AGENTENREGELN_A.md` mit den Nutzerentscheidungen. Die
Regel „nur `src/`, `werkzeuge/` und `*.md` versionieren“ bleibt und wird durch
die Datenprüfung der CI abgesichert.

Runner: `vba`, `office`, `nativ` (Windows-Lauf), dazu ein Profil `mac` für den
Probelauf in Excel für Mac (nur lokal).

### 8.5 P-PROT (Access + Word)

| bisher (Fassungsordner) | künftig |
|---|---|
| `Module/` von Hand bzw. per Skript aus `src/` erzeugt | `office.access.to_import_files` im Build |
| `Pruefung/…werkzeug_regelgate-lokal.py`, `…werkzeug_mcp-intern.py` | `gate mcp` mit Endpunktprofilen `lokal` (eigener Regelserver) und `intern` |
| Gastskripte für Lauf, Phasen und Klickprobe | `access lauf` (Schritte RUN/ZAHL/WORD/FOTO), `word`-Prozesskontrolle vorher/nachher, Klickprobe |
| Paketbau `gesamtpaket_ergaenzen.py`, `test_gesamtpaket.py`, `PAKET_SHA256.json` | `liefern paket/pruefen` mit Paketlayout (LIESMICH, CHANGELOG, `src/`, `Module/`, `Pruefung/`) |
| Soll-Zähler im LIESMICH (Quellen, Sitzungen, TOPs, Beschlüsse, Befunde) | `sollwerte.json` + `abnahme pruefen` gegen die ZAHL-Zeilen |

Bleibt im Projekt: `src/`, LIESMICH/CHANGELOG je Fassung, Python-Tests des
XML-Lesewegs, die Testprotokolle **nur lokal** (echte Dokumente, nie im Repo
und nie in der CI). Runner: `access`, `office`, `nativ` (mit Word-Weg).

### 8.6 CI-Workflow: statische Prüfung ohne Daten

Jedes Projekt-Repo ruft einen wiederverwendbaren Workflow aus auditcore auf
(E15), gepinnt per Commit-SHA:

```yaml
# .github/workflows/vba-statisch.yml (im Projekt-Repo)
name: vba-statisch
on: { push: { branches: [main] }, pull_request: {} }
permissions: { contents: read }
concurrency: { group: flowaudit-mcp-${{ github.repository }}, cancel-in-progress: true }
jobs:
  statisch:
    uses: <auditcore-repo>/.github/workflows/officebank-statisch.yml@<commit-sha>
    with:
      host: access                 # excel | access | word
      officebank-version: 0.1.0    # hashgebunden aus dem Paketindex
      mcp-endpunkt: oeffentlich
    secrets:
      flowaudit-mcp-token: ${{ secrets.FLOWAUDIT_MCP_TOKEN }}
```

Schritte des Workflows:

1. Checkout ohne Persistenz der Anmeldedaten, Python, `auditcore_officebank`
   hashgebunden installieren.
2. **Datenfreiheit des Repos:** keine verbotenen Endungen und Ordner, kein
   Treffer der Muster des Datenschutz-Gates (`gate datenschutz --nur-muster`),
   gitleaks.
3. `gate ascii --pruefen`, `gate lint`, `gate lint-sql` (bei Access).
4. **Lokalen Nachweis prüfen** (`gate nachweis-pruefen`): Der Nachweis des
   Namensabgleichs aus dem Pre-push-Hook muss zum Manifest des Commits passen
   und 0 Treffer zeigen (E14). Fehlt er, ist der Lauf rot.
5. `gate mcp` mit der vollständigen Modulmenge über den Sitzungsweg. Ein Job
   je Repo zur selben Zeit (Concurrency, wegen `max_concurrent = 2`),
   Teilmengen bei Zeitlimit, Paginierung vollständig. Kriterium ist
   `errors = 0`, und jede Warnung muss im Repo begründet sein.
6. Artefakte: nur JUnit, maskierter Gate-Nachweis und Befundliste. Keine
   Ergebnisse, keine Protokolle aus Office-Läufen.
7. Status im Step-Summary: `native_office_compile = not_run`. Die CI kompiliert
   nie in Office und behauptet das auch nicht.

Rahmenbedingungen: GitHub-gehostete Runner genügen, weil nur Quelltext
übertragen wird. Wer auf eigene Runner geht, nutzt `auditcore-runner`
(Fork- und Dependabot-Schutz wie im auditcore-Repo). Actions werden per SHA
gepinnt, zizmor und actionlint prüfen den Workflow im auditcore-Repo. Das Token
ist ein eigenes CI-Token des MCP mit Rechten nur auf die `vba_*`- und
`access_check_*`-Werkzeuge.

---

## Nutzerentscheidungen 05.10.2026

Verbindlich: **alle Entscheidungen wie empfohlen.**

| Nr. | Entscheidung |
|---|---|
| E01 | Plan wie vorgelegt (a) |
| E02 | ein Paket `auditcore_officebank` mit Extras `[docx]` und `[xlsx]` |
| E03 | Plugin im Monorepo unter `plugins/auditcore-office/` |
| E04 | Lizenz MIT |
| E05 | QChess: nur der generische SQL-Server-Dienst ist öffentlich, der Client bleibt privates Projektprofil |
| E06 | macOS mit UTM zuerst, Backend-Schnittstelle für libvirt vorbereitet |
| E07 | HTTP-Austauschserver mit Token als Standard, SPICE-WebDAV optional |
| E08 | Python-API englisch, CLI und Meldungen deutsch |
| E09 | begründete Abweichungen als TOML |
| E10 | eigener MCP-Client mit Standardbibliothek |
| E11 | Sperrdatei mit TTL in 0.1 |
| E12 | Pilot P-ACC zuerst, danach P-XL1, P-XL2 und P-PROT parallel |
| E13 | Plan bleibt unter `docs/projekt/` |
| E14 | Muster-Gate in der CI plus lokaler Nachweis des Namensabgleichs |
| E15 | wiederverwendbarer Workflow `officebank-statisch` im auditcore-Repo |
| E16 | privates Repo für P-PROT ist vorhanden |

Umsetzungsstand: Etappe 0 (Gerüst) – Paket `packages/auditcore_officebank`
0.1.0 (unveröffentlicht) und Plugin-Gerüst `plugins/auditcore-office/`.
