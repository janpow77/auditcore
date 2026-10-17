// ESLint-Konfiguration der JavaScript-/TypeScript-Pakete (packages-js).
import js from '@eslint/js'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import pluginVue from 'eslint-plugin-vue'
import reactHooks from 'eslint-plugin-react-hooks'

export default tseslint.config(
  { ignores: ['**/dist/**', '**/dist-*/**', '**/e2e-results/**', '**/node_modules/**', '**/coverage/**'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['packages-js/**/*.{ts,tsx,mts}', 'scripts/js/**/*.mjs'],
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      complexity: ['error', 12],
      'max-lines-per-function': ['warn', { max: 60, skipBlankLines: true, skipComments: true }],
      'max-lines': ['warn', { max: 400, skipBlankLines: true, skipComments: true }],
      'no-restricted-syntax': [
        'error',
        {
          selector: 'Program > :first-child[type="EmptyStatement"]',
          message: 'Leere Anweisung am Dateianfang',
        },
      ],
    },
  },
  // Vue-SFC (packages-js/ui): Vue-Regeln, TypeScript im <script setup>, höchstens 250 Zeilen je SFC.
  ...pluginVue.configs['flat/recommended'].map((config) => ({ ...config, files: ['packages-js/**/*.vue'] })),
  {
    files: ['packages-js/**/*.vue'],
    languageOptions: {
      parserOptions: { parser: tseslint.parser, extraFileExtensions: ['.vue'] },
      globals: { ...globals.browser },
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      complexity: ['error', 12],
      'max-lines': ['error', { max: 250, skipBlankLines: false, skipComments: false }],
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/multiline-html-element-content-newline': 'off',
      'vue/html-self-closing': 'off',
      'vue/multi-word-component-names': 'off',
    },
  },
  // Native React-Komponenten und framework-freier Kern: strengere Grenzen (McCabe ≤ 10,
  // Funktionen ≤ 60 Zeilen, Komponentendateien ≤ 250 Zeilen wie Vue-SFC).
  {
    files: ['packages-js/ui-react/src/**/*.{ts,tsx}', 'packages-js/ui-core/src/**/*.ts', 'packages-js/kanban-core/src/view/**/*.ts'],
    plugins: { 'react-hooks': reactHooks },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'error',
      complexity: ['error', 10],
      'max-lines-per-function': ['error', { max: 60, skipBlankLines: true, skipComments: true }],
    },
  },
  // BPMN: native React-Oberfläche und framework-freier UI-Kern mit denselben Grenzen.
  {
    files: ['packages-js/bpmn-react/src/**/*.{ts,tsx}', 'packages-js/bpmn-flowaudit/src/ui/**/*.ts'],
    plugins: { 'react-hooks': reactHooks },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'error',
      complexity: ['error', 10],
      'max-lines-per-function': ['error', { max: 60, skipBlankLines: true, skipComments: true }],
      'max-lines': ['error', { max: 250, skipBlankLines: false, skipComments: false }],
    },
  },
  // Stichprobenvorlagen: Kern und Vue-Bindung von Anfang an mit den Maßstäben für neue Module.
  {
    files: ['packages-js/sampling-templates-core/src/**/*.ts', 'packages-js/sampling-templates-vue/src/**/*.{ts,vue}'],
    rules: {
      complexity: ['error', 10],
      'max-lines-per-function': ['error', { max: 60, skipBlankLines: true, skipComments: true }],
    },
  },
  // Rechenkerne der Stichprobenvorlagen: Vergleiche auf Rechenwerten nur mit der Toleranz der
  // Tabellenkalkulation (eq, ne, lt, le, gt, ge aus src/excel), nie mit den Operatoren der Sprache.
  {
    files: ['packages-js/sampling-templates-core/src/sheets/**/*.ts'],
    rules: {
      'no-restricted-syntax': [
        'error',
        { selector: 'Program > :first-child[type="EmptyStatement"]', message: 'Leere Anweisung am Dateianfang' },
        { selector: 'BinaryExpression[operator=/^(<|>|<=|>=)$/]', message: 'Vergleich wie in der Tabellenkalkulation: lt, le, gt, ge aus src/excel verwenden.' },
        { selector: 'BinaryExpression[operator=/^[!=]==$/][right.type="Literal"][right.raw=/^-?[0-9]/]', message: 'Zahlenvergleich wie in der Tabellenkalkulation: eq, ne oder sameNumber aus src/excel verwenden.' },
        { selector: 'BinaryExpression[operator=/^[!=]==$/][left.type="Literal"][left.raw=/^-?[0-9]/]', message: 'Zahlenvergleich wie in der Tabellenkalkulation: eq, ne oder sameNumber aus src/excel verwenden.' },
      ],
    },
  },
  {
    files: ['packages-js/**/src/**/*.tsx'],
    rules: {
      'max-lines': ['error', { max: 250, skipBlankLines: false, skipComments: false }],
    },
  },
  {
    files: ['packages-js/**/test/**/*.{ts,tsx}'],
    rules: {
      'max-lines-per-function': 'off',
      'max-lines': 'off',
    },
  },
)
