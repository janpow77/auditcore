# Anbindung eines Fachpakets an auditcore_common

1. **Abhängigkeit mit exaktem Pin:** in `pyproject.toml`
   `dependencies = ["auditcore_common==0.1.1"]`; braucht das Paket sicheres XML,
   dann im eigenen Extra `auditcore_common[xml]==0.1.1`. Das APT-Paket
   `python3-auditcore-common` wird aus dem Pin abgeleitet
   (`scripts/verify_domain_packages.py`). `tests/installed_smoke.py` des Pakets
   prüft die Laufzeitanforderungen – dort den Pin nachziehen.
2. **Architekturtest:** `auditcore_common` in die erlaubten Wurzelimporte
   aufnehmen (Top-Level-Import erlaubt, nur Standardbibliothek).
3. **Aufruf mit paketeigenem Fehler:** Die Funktionen nehmen die Fehlerklasse
   oder eine Fehlerfabrik entgegen, zum Beispiel

   ```python
   from auditcore_common.profiles import load_packaged_profile

   def load_profile(profile_id: str, version: str) -> Profile:
       return load_packaged_profile(
           "auditcore_x.profile_data", profile_id, version,
           parse=profile_from_dict, identity=lambda p: (p.id, p.version),
           error=ProfileError, require_text=True, invalid_name="invalid",
       )
   ```

   Die Variante (Parameter) muss der bisherigen Kopie entsprechen; welche das
   ist, steht je Paket in `docs/quality/duplikate.md` (Tabelle A).
4. **Namen:** interne Kopien entfallen. Öffentliche Hilfsnamen bleiben als Alias
   mit `DeprecationWarning`; fachliche Einstiegspunkte (`load_profile`,
   `fingerprint`, …) bleiben als dünne Funktionen ohne Warnung.
5. **Nachweis:** Die bestehenden Charakterisierungs- und Replaytests des Pakets
   müssen unverändert grün bleiben; Patch-Version erhöhen, Code-Gate-Baseline
   per `--update-baseline` absenken.
