# Abgrenzung zu bestehenden Anwendungen

Die Bibliothek ist neu geschrieben; es wurde kein Code übernommen und kein
Anwendungsverhalten charakterisiert.

- **audit_designer, Modul flowstat** (`sampling_service.run_error_projection`,
  `run_precision_calculation`): rechnet mit Endlichkeitskorrektur und für MUS mit
  der mittleren Fehlerquote × Buchwert; beides weicht von den Formeln des
  Leitfadens ab (6.1.1.4, 6.3.1.4). Eine Umstellung auf diese Bibliothek ändert
  daher Ergebnisse und braucht eine fachliche Entscheidung.
- **audit-portal** (`rer_service.compute_rer`): setzt dieselbe Vorlage Annex 3
  mit `Decimal` um. Die Zeilen A–M sind gleich definiert; die Bibliothek prüft
  zusätzlich die Wesentlichkeitsschwelle (≤ 2 %) und verlangt nicht negative
  Beträge für E1, E2 und H.
- **auditcore_sampling**: bleibt zuständig für Stichprobenumfang und Auswahl.
  Die KOM-Formeln für den Umfang (z. B. n = (z × BV × σ_r/(TE − AE))² oder
  n = BV × RF/(TE − AE × EF)) sind dort noch nicht enthalten.
