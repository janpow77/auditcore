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
    files: ['packages-js/ui-react/src/**/*.{ts,tsx}', 'packages-js/ui-core/src/**/*.ts'],
    plugins: { 'react-hooks': reactHooks },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'error',
      complexity: ['error', 10],
      'max-lines-per-function': ['error', { max: 60, skipBlankLines: true, skipComments: true }],
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
