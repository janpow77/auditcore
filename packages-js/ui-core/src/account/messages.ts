import { defineMessages } from '../i18n'
export const accountMessages = defineMessages({
  de: {
    crop: 'Quadratisch zuschneiden', zoom: 'Zoom', horizontal: 'Horizontaler Ausschnitt', vertical: 'Vertikaler Ausschnitt',
    title: 'Konto und Organisation', loading: 'Daten werden geladen …', empty: 'Keine Einträge vorhanden.',
    failed: 'Anfrage abgelehnt: {message}', choose: 'Wählen Sie einen Bereich aus.',
    save: 'Änderungen speichern', discard: 'Änderungen verwerfen', saved: 'Änderungen gespeichert.',
    dirty: 'Ungespeicherte Änderungen. Bitte speichern oder verwerfen, bevor Sie den Bereich wechseln.',
    readonly: 'Diese Angaben werden zentral verwaltet.', preview: 'Vorschau', camera: 'Webcam aktivieren',
    capture: 'Foto aufnehmen', stop: 'Kamera schließen', upload: 'Bild auswählen', remove: 'Bild entfernen',
    cameraFailed: 'Kamera nicht verfügbar. Bitte ein Bild auswählen.',
  },
  en: {
    crop: 'Crop square', zoom: 'Zoom', horizontal: 'Horizontal crop position', vertical: 'Vertical crop position',
    title: 'Account and organisation', loading: 'Loading data …', empty: 'No entries.',
    failed: 'Request rejected: {message}', choose: 'Choose a section.',
    save: 'Save changes', discard: 'Discard changes', saved: 'Changes saved.',
    dirty: 'Unsaved changes. Save or discard before switching sections.',
    readonly: 'These details are managed centrally.', preview: 'Preview', camera: 'Enable webcam',
    capture: 'Take photo', stop: 'Close camera', upload: 'Choose image', remove: 'Remove image',
    cameraFailed: 'Camera unavailable. Please choose an image.',
  },
})
export type AccountMessageKey = keyof typeof accountMessages.de
