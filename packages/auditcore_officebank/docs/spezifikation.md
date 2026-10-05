# Spezifikation `auditcore_officebank` (Stand Etappe 0)

Verbindliche Planung: [Plan 0.1](../../../docs/projekt/20261005_Plan_auditcore_officebank_0.1.md)
mit den Nutzerentscheidungen vom 05.10.2026. Dieses Dokument hält fest, was je
Etappe umgesetzt ist; Details stehen im Plan.

## Etappenstand

| Etappe | Inhalt | CLI-Gruppen | Stand |
|---:|---|---|---|
| 0 | Gerüst: Konfiguration, Schemas, Maskierung, Fakes, CLI-Rahmen | `status`, `konfig` | umgesetzt |
| 1 | Gates: ascii, lint-vba, lint-sql, datenschutz, MCP-Client | `gate` | geplant |
| 2 | VM: UTM-Backend, Austauschserver mit Token, Benutzersitzung, Sperre | `vm` | geplant |
| 3 | Office: Excel (Windows und Mac), Access, Word | `excel`, `access`, `word` | geplant |
| 4 | Build, Abnahme, Lieferung | `build`, `abnahme`, `liefern` | geplant |
| 5 | Generischer SQL-Server-Testdienst | `mssql` | geplant |
| 6 | Runner-Profile, Plugin `auditcore-office`, CI-Vorlage | `projekt`, `runner-profil` | geplant |

Geplante Gruppen sind in der CLI angelegt und enden mit Exit 3, damit Skripte
und Plugin-Skills den Stand ohne Raten erkennen.

## Unterpakete

| Unterpaket | Inhalt in Etappe 0 |
|---|---|
| `config` | Rechnerprofil, Projektdatei, Schemaversion, `migrate` (nur Version 1) |
| `masking` | Ausgabefilter für Token, Passwörter, Verbindungszeichenfolgen |
| `stages` | Zuordnung CLI-Gruppe → Etappe |
| `vm` | `GuestBackend` (Protocol), `GuestResult`, `VmState` |
| `testing` | `FakeGuest` |
| `office`, `mssql`, `builder`, `acceptance`, `gates`, `delivery`, `project` | Docstrings und Typgerüste |

## Schemas

| Schema | Datei | Paketdaten |
|---|---|---|
| `auditcore-officebank/rechner/1` | `~/.config/auditcore-officebank/profil.toml` | `data/schemas/rechner.schema.json` |
| `auditcore-officebank/projekt/1` | `.officebank.toml` im Projekt-Repo | `data/schemas/projekt.schema.json` |

Eine neue Schemaversion braucht eine Migration in `config.migrate` und Tests mit
der alten Fassung.
