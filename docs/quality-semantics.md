# Quality-Gate-Semantik

Befundstatus und Prozess-Exitcode sind getrennt. Exit 1 bedeutet einen
nachgewiesenen technischen Fehler; `--strict` behandelt technische Warnungen
zusätzlich als Fehler. Exit 2 bedeutet einen ungültigen Aufruf/technischen Abbruch.
Ein Exitcode 0 behauptet bei REVIEW_REQUIRED oder NOT_EXECUTED ausdrücklich
keinen vollständig bestandenen Prüfstatus. Diese Statuswerte bleiben im JSON.
Unbekannte Anwendbarkeit wird nicht künstlich in einen Compliance-FAIL umgewandelt.
Refactoring und Deployment prüfen die relevanten Policy- und Testnachweise
zusätzlich; ein CLI-Exitcode allein erzeugt niemals READY_FOR_DEPLOYMENT.

`src/auditcore` bezeichnet den Fachkern; die vier Werkzeuge werden in ihren
separaten Verzeichnissen geprüft. Die Core-Prüfung schließt das Unterverzeichnis
`tools` deshalb aus. Die expliziten Tool-Self-Checks prüfen dessen Code vollständig.
Quelltext-Ignore-Kommentare werden im Report separat aufgeführt. Potenzielle
Credentials können nicht per Quelltextkommentar ausgeblendet werden.

Grenzen: AST-Aufrufbeziehungen können dynamische Bindungen nicht beweisen.
Gleiche AST-Strukturen sind keine fachliche Freigabe. Bandit, Mypy, pip-audit und
Ruff werden als separate Prozesse ausgeführt; Abwesenheit/Timeout bleibt sichtbar.
Der Prüfkatalog liefert anwendbare Akzeptanzfälle, keine bereits bestandenen Tests.
