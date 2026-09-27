# Runner-Backends

Beide Backends starten Runner gleich: je Instanz eine systemd-User-Unit
(`auditcore-runner-<klasse>@<n>`), je Job eine Einmal-Registrierung und ein
frischer Container. Sie unterscheiden sich darin, woher die Registrierung und
die Nachfrage kommen.

| | `jit` (Standard) | `scaleset` |
|---|---|---|
| Registrierung | REST `generate-jitconfig` mit Labels der Klasse | `generatejitconfig` des Scale-Sets der Klasse |
| Auswahl im Workflow | `runs-on: [self-hosted, …]` (Labels) | `runs-on: <praefix>-<klasse>` (Scale-Set-Name) |
| Nachfrage | Soll-Quelle (`statisch`, `lokal`, `datei`); `lokal` fragt die REST-API nach wartenden Jobs | Listener: Long-Poll, `totalAssignedJobs` |
| Zusätzliche Unit | – | `auditcore-runner-scaleset.service` (`scaleset lauschen`) |

## Scale-Set-Backend

Umsetzung des Protokolls des MIT-lizenzierten Referenzclients
[`actions/scaleset`](https://github.com/actions/scaleset) in Python
(`scaleset.py`, API-Version `6.0-preview` fest; Lizenz in
`LICENSES/actions-scaleset-MIT.txt`):

1. Registrierungstoken (REST) → Admin-Verbindung zum Actions-Dienst
   (`/actions/runner-registration`), erneuert kurz vor Ablauf.
2. Je aktiver Klasse ein Scale-Set `<praefix>-<klasse>` in der Runner-Gruppe
   (angelegt, falls es fehlt; Runner ohne Selbstaktualisierung).
3. Je Scale-Set eine Nachrichten-Sitzung; der Listener holt Nachrichten per
   Long-Poll (Kopfzeile `X-ScaleSetMaxCapacity` = Kapazität), wertet die
   Statistik aus und löscht jede Nachricht (`DeleteMessage`). Ein abgelaufenes
   Warteschlangen-Token erneuert die Sitzung.
4. Soll je Klasse = min(Kapazität, `min_instanzen` + `totalAssignedJobs`);
   Kapazität = `max_instanzen`, gesenkt durch die Soll-Quelle (z. B. lokaler
   Regler). Beides landet in der Nachfrage-Datei, die Supervisoren halten sich
   daran. Ist der Listener aus (Datei älter als 5 Minuten), gilt nur noch die
   Soll-Quelle – Runner bleiben nutzbar.
5. Beim Stoppen löscht der Listener seine Sitzungen; `scaleset loeschen`
   entfernt die Scale-Sets.

Eine Sitzung je Scale-Set ist erlaubt; zwei Rechner brauchen deshalb
verschiedene Präfixe. Wechsel `jit` → `scaleset`: Profil ändern,
`runner install` (legt die Listener-Unit an), Workflows auf den
Scale-Set-Namen umstellen. JIT bleibt Standard, bis Scale-Sets auf dem
eigenen Rechner erprobt sind.

## Rückfall auf gehostete Runner

`auditcore-runner workflows vorlage runner-wahl --ziel .github/workflows`
kopiert einen wiederverwendbaren Entscheidungs-Job (`workflow_call`). Er liefert
`runs-on` als JSON: eigene Runner, wenn mindestens einer mit dem angegebenen
Label online ist (optional, mit einem nur lesenden Token), sonst den Rückfall
(`ubuntu-latest`); Fork-PRs und Dependabot immer auf den Rückfall. Einbindung
und Rechte stehen im Kopf der Vorlage.
