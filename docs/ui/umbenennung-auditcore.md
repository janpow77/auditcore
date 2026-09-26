# Umbenennung des npm-Scopes: `@flowaudit` → `@auditcore`

Ab dem Release nach v0.4.1 heißen alle JS-Pakete unter `packages-js/`
`@auditcore/<paket>`, einheitlich mit den Python-Paketen `auditcore_*`.
Unter dem alten Scope `@flowaudit` wurde auf npm nie etwas veröffentlicht;
betroffen sind nur Anwendungen, die Tarballs aus `frontend/vendor/` oder
Workspace-Verweise nutzen.

| Alt | Neu |
|---|---|
| `@flowaudit/common` | `@auditcore/common` |
| `@flowaudit/ui-core` | `@auditcore/ui-core` |
| `@flowaudit/ui` | `@auditcore/ui` |
| `@flowaudit/ui-react` | `@auditcore/ui-react` |
| `@flowaudit/kanban-core` | `@auditcore/kanban-core` |
| `@flowaudit/bpmn-editor` | `@auditcore/bpmn-editor` |
| `@flowaudit/bpmn-flowaudit` | `@auditcore/bpmn-flowaudit` |
| `@flowaudit/bpmn-vue` | `@auditcore/bpmn-vue` |
| `@flowaudit/bpmn-react` | `@auditcore/bpmn-react` |
| Tarball `flowaudit-<paket>-<version>.tgz` | `auditcore-<paket>-<version>.tgz` |
| `.npmrc`: `@flowaudit:registry=…` | `@auditcore:registry=…` |
| npm-Organisation `flowaudit` | `auditcore` |

**Unverändert** bleiben Web-Component-Tags (`<flowaudit-table>`,
`<flowaudit-bpmn-editor>` …), Komponenten- und Funktionsnamen
(`FlowauditTable`, `createFlowauditUi`, `defineFlowauditElements`),
CSS-Variablen (`--fa-*`), Klassennamen, Unterpfade der Exporte
(`/elements`, `/style.css`, `/browser`) und die Paketversionen. Die
Umbenennung ist rein namentlich; APIs und Verhalten ändern sich nicht.

## Anwendung umstellen

1. **Imports ersetzen** (Quellcode, Tests, Konfiguration):

   ```bash
   git grep -l '@flowaudit/' -- ':!**/CHANGELOG.md' \
     | xargs sed -i 's#@flowaudit/#@auditcore/#g'
   ```

   Das erfasst `import … from '@flowaudit/ui'`, CSS-Imports
   (`@flowaudit/ui/style.css`), Vite-/Vitest-Aliase, `tsconfig`-`paths`,
   `optimizeDeps`, ESLint-Regeln (`no-restricted-imports`) und Mocks
   (`vi.mock('@flowaudit/…')`). Reguläre Ausdrücke wie `/^@flowaudit\//`
   gesondert suchen: `git grep -n '@flowaudit'`.

2. **Vendor-Tarballs austauschen** (Ablage nach
   [frontend-installation.md](../deployment/frontend-installation.md)):
   die Tarballs des neuen Releases (`auditcore-<paket>-<version>.tgz`) nach
   `frontend/vendor/` legen, alte `flowaudit-*.tgz` samt
   `*.provenance.json` löschen und die Herkunftsdateien neu schreiben
   (Dateiname, SHA-256, npm-Integrität aus `npm-packages.json` des Releases).
   In `package.json`:

   ```json
   "@auditcore/ui": "file:vendor/auditcore-ui-<version>.tgz"
   ```

   Alle internen Pakete der Abhängigkeitshülle gemeinsam umstellen; ein
   Gemisch aus `@flowaudit/*` und `@auditcore/*` installiert zwei getrennte
   Kopien des Kerns.

3. **Registry-Sperre anpassen:** in `frontend/.npmrc`
   `@flowaudit:registry=…` durch `@auditcore:registry=https://npm-registry.invalid/`
   ersetzen (solange die App nicht aus npmjs.org installiert).

4. **Lock neu erzeugen:** `rm -rf node_modules && npm install`, danach
   `git grep -n '@flowaudit'` – außer in Changelogs darf nichts übrig sein.
   Dann `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.

5. **Docker/CI:** Build-Schritte, die Tarballs per Name kopieren
   (`COPY vendor/flowaudit-*.tgz`), und Dependabot-/Renovate-Regeln auf den
   neuen Scope umstellen.

Nach der ersten npm-Veröffentlichung reicht statt Schritt 2–3
`npm install @auditcore/<paket>@<version>`.
