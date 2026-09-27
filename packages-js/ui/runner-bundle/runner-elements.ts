/**
 * Eigenständiges Bündel der Runner-Konsole für die lokale Oberfläche von
 * `auditcore_runner` (`auditcore-runner ui`): Vue, Kern und Stile sind
 * enthalten, registriert wird nur `<flowaudit-runner-console>`.
 */
import stile from '@auditcore/ui-core/style.css?inline'
import { defineElement } from '../src/elements/define'
import { runnerConsoleElement } from '../src/runner/element'

const style = document.createElement('style')
style.dataset.flowaudit = 'runner'
style.textContent = stile
document.head.append(style)
defineElement(runnerConsoleElement)
