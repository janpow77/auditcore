# Hooks (geplant, Etappe 6)

Noch keine `hooks.json`: Das Plugin registriert in Etappe 0 bewusst keine Hooks.

| Hook | Ereignis | Wirkung |
|---|---|---|
| `kein-sammelcommit` | PreToolUse (Bash) | blockiert `git commit -a`, `git add -A`, `git add .` und `git reset --hard` in Office-Projekten |
| `vba-geaendert` | PostToolUse (Write/Edit auf `*.bas`, `*.cls`, `*.frm`) | führt `gate ascii --pruefen` und `gate lint` für die Datei aus und erinnert an den MCP-Vorlauf |
| `vm-sperre` | PreToolUse (Bash mit `auditcore-officebank vm nutzer` oder `build lauf`) | verweigert ohne eigene Sperre |
| `keine-secrets` | PostToolUse (Bash) | maskiert Ausgaben mit Token-, Passwort- oder Verbindungszeichenfolgen-Mustern und warnt |
