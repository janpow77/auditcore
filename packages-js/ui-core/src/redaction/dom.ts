// Fokusführung von „PDF schwärzen“ (Vue und React gleich): Der Fokus fällt nie auf <body> zurück.

/** Nach einem Schrittwechsel (Prüfansicht, Ergebnis, Formular) die Überschrift des neuen Schritts fokussieren. */
export function focusRedactionHeading(root: Element | null | undefined): void {
  root?.querySelector<HTMLElement>('.fa-redaction__heading')?.focus()
}

/** Nach dem Entfernen eines eigenen Bereichs: Fokus auf „Bereich hinzufügen“ derselben Komponente. */
export function focusRedactionAddArea(from: Element | null | undefined): void {
  from?.closest('.fa-redaction')?.querySelector<HTMLElement>('[data-testid="redaction-add-area"]')?.focus()
}
