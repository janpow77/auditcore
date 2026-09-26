# Testdaten

Alle Diagramme in `synthetic/` sind **synthetisch**. Sie bilden die Struktur
der ausgewerteten Nutzerdiagramme nach (Lanes mit Freitext-Namen,
Rollenpräfixe in Aufgaben, Normzitate und Fundstellen in
`bpmn:documentation`, Bewertungskriterien, Feststellungsbezüge, Prüffelder,
Registerkürzel, Rotfärbungen), enthalten aber keine echten Behörden-,
Programm-, Firmen- oder Personennamen, keine echten Beträge und keine
Prüfbefunde. Sie gelten für das Profil `foerderperiode-2021-2027`.

Nutzerdiagramme werden **nicht** ins Repository übernommen. Paritätstests
gegen sie laufen nur lokal:

```bash
AUDITCORE_BPMN_LOCAL_FIXTURES=/pfad/zu/gdrive-bpmn pytest tests/test_local_user_diagrams.py
```

`legacy_observed.json` hält die beobachteten Ausgaben der Originale aus
audit_designer fest (`tools/capture_legacy.py`, synthetische Eingaben).
