# Copyleft-Programme im Runner-Image: Lizenztexte und Quellen

Diese Programme liegen nur als separate, unveränderte Programme im Image. Sie
werden als eigener Prozess aufgerufen; kein Code daraus ist in `auditcore_runner`
übernommen oder damit verlinkt. Der vollständige Quelltext der jeweils
ausgelieferten Version ist unter dem angegebenen Tag erhältlich.

| Programm | Version im Image | Lizenz | Lizenztext | Quelltext |
|---|---|---|---|---|
| Opengrep | 1.30.0 | LGPL-2.1 | `opengrep-LGPL-2.1.txt` | https://github.com/opengrep/opengrep/tree/v1.30.0 |
| codespell | 2.4.3 | GPL-2.0-only | `codespell-GPL-2.0.txt` | https://github.com/codespell-project/codespell/tree/v2.4.3 |
| axe-core (über @axe-core/playwright) | 4.13.0 | MPL-2.0 | `axe-core-MPL-2.0.txt` | https://github.com/dequelabs/axe-core/tree/v4.13.0 |
| lightningcss (Abhängigkeit von vitest) | 1.33.0 | MPL-2.0 | `lightningcss-MPL-2.0.txt` | https://github.com/parcel-bundler/lightningcss/tree/v1.33.0 |

Im Image liegen diese Dateien unter `/usr/share/doc/auditcore-runner/LICENSES/`.
