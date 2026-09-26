# Beispielprojekte

Minimale Anwendungen, die die npm-Pakete aus `packages-js/` so einbinden wie
eine fremde Anwendung: ausschließlich über `npm pack`-Tarballs, ohne Workspace.
Anleitung: [docs/deployment/frontend-installation.md](../docs/deployment/frontend-installation.md).

| Beispiel | Inhalt |
|---|---|
| [`vue-minimal`](vue-minimal) | Vue 3 mit `@auditcore/ui`: Plugin, Tabelle, Hell/Dunkel, Sprachwechsel |
| [`react-minimal`](react-minimal) | React 18 mit den nativen Komponenten aus `@auditcore/ui-react`, ohne Vue |
| [`webcomponent-minimal`](webcomponent-minimal) | `<flowaudit-table>` per `<script type="module">` und Import-Map, ohne Bundler |

In `package.json` stehen die `@auditcore`-Pakete als `file:../vendor/<paket>.tgz`.
Das Prüfskript ersetzt diese Angaben in einer frischen Kopie durch die Tarballs
des Workspace oder eines Releases, sperrt die Registry für `@auditcore`,
installiert, gleicht `package-lock.json` ab und baut:

```bash
npm ci && npm run build                                   # im Repository-Stamm
node scripts/js/verify-examples.mjs                       # Tarballs aus dem Workspace
node scripts/js/verify-examples.mjs --base-url https://github.com/janpow77/auditcore/releases/download/v<release>
node scripts/js/verify-examples.mjs --only react-minimal --keep   # Arbeitsverzeichnis behalten
```

Die CI (Workflow `js-packages`) führt die erste Variante bei jeder Änderung an
`packages-js/` oder `examples/` aus. In einer echten Anwendung stehen statt
`file:../vendor/…` die Release-URLs oder eine `vendor/`-Ablage mit
Herkunftsdatei.
