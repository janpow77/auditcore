//#region ../ui-core/styles/index.css?inline
var e = ":where(:root,[data-fa-theme]){--fa-font-sans:\"IBM Plex Sans\", \"Source Sans 3\", system-ui, -apple-system, \"Segoe UI\", sans-serif;--fa-font-mono:\"IBM Plex Mono\", ui-monospace, \"SFMono-Regular\", Menlo, monospace;--fa-font-size-xs:.75rem;--fa-font-size-sm:.8125rem;--fa-font-size-md:.9375rem;--fa-font-size-lg:1.125rem;--fa-line-height:1.45;--fa-space-1:.25rem;--fa-space-2:.5rem;--fa-space-3:.75rem;--fa-space-4:1rem;--fa-space-5:1.5rem;--fa-space-6:2rem;--fa-radius-sm:4px;--fa-radius:8px;--fa-radius-lg:12px;--fa-color-bg:#f4f5f2;--fa-color-surface:#fff;--fa-color-surface-raised:#fbfbf9;--fa-color-surface-sunken:#eceee9;--fa-color-text:#1b2230;--fa-color-text-muted:#5b6474;--fa-color-border:#d6d9d2;--fa-color-border-strong:#a9aea4;--fa-color-accent:#1f5f8b;--fa-color-accent-hover:#174a6d;--fa-color-accent-contrast:#fff;--fa-color-accent-soft:#e3eef6;--fa-color-danger:#b42318;--fa-color-danger-soft:#fdecea;--fa-color-warning:#a15c07;--fa-color-warning-soft:#fdf1dc;--fa-color-success:#1d7a46;--fa-color-success-soft:#e3f4ea;--fa-color-overlay:#0f141c73;--fa-shadow-sm:0 1px 2px #141a2414;--fa-shadow:0 2px 6px #141a241a, 0 1px 2px #141a240f;--fa-shadow-lg:0 18px 40px #141a242e;--fa-focus-ring:0 0 0 3px #1f5f8b59;--fa-transition:.14s ease;--lightningcss-light:initial;--lightningcss-dark: ;color-scheme:light}@media (prefers-color-scheme:dark){:where(:root:not([data-fa-theme=light])){--fa-color-bg:#101318;--fa-color-surface:#181c23;--fa-color-surface-raised:#1f242c;--fa-color-surface-sunken:#0c0f13;--fa-color-text:#e6e9ee;--fa-color-text-muted:#9aa3b2;--fa-color-border:#2c323c;--fa-color-border-strong:#4a5260;--fa-color-accent:#6fb1e0;--fa-color-accent-hover:#93c6ea;--fa-color-accent-contrast:#0c1a26;--fa-color-accent-soft:#1b3346;--fa-color-danger:#f0877d;--fa-color-danger-soft:#3a1c1a;--fa-color-warning:#e7b35f;--fa-color-warning-soft:#3a2c14;--fa-color-success:#6fcf97;--fa-color-success-soft:#173323;--fa-color-overlay:#0009;--fa-focus-ring:0 0 0 3px #6fb1e073;--lightningcss-light: ;--lightningcss-dark:initial;color-scheme:dark}}:where([data-fa-theme=dark]){--fa-color-bg:#101318;--fa-color-surface:#181c23;--fa-color-surface-raised:#1f242c;--fa-color-surface-sunken:#0c0f13;--fa-color-text:#e6e9ee;--fa-color-text-muted:#9aa3b2;--fa-color-border:#2c323c;--fa-color-border-strong:#4a5260;--fa-color-accent:#6fb1e0;--fa-color-accent-hover:#93c6ea;--fa-color-accent-contrast:#0c1a26;--fa-color-accent-soft:#1b3346;--fa-color-danger:#f0877d;--fa-color-danger-soft:#3a1c1a;--fa-color-warning:#e7b35f;--fa-color-warning-soft:#3a2c14;--fa-color-success:#6fcf97;--fa-color-success-soft:#173323;--fa-color-overlay:#0009;--fa-focus-ring:0 0 0 3px #6fb1e073;--lightningcss-light: ;--lightningcss-dark:initial;color-scheme:dark}.fa-sr-only{clip:rect(0, 0, 0, 0);white-space:nowrap;border:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}@media (prefers-reduced-motion:reduce){:where([data-fa-theme],:root){--fa-transition:0s linear}}.fa-icon{stroke-width:var(--fa-icon-stroke,1.75);vertical-align:middle;flex:none}.fa-badge{align-items:center;gap:var(--fa-space-1);padding:.125rem var(--fa-space-2);font:600 var(--fa-font-size-xs) / 1.3 var(--fa-font-sans);background:var(--fa-color-surface-sunken);color:var(--fa-color-text-muted);border-radius:999px;display:inline-flex}.fa-badge--accent{background:var(--fa-color-accent-soft);color:var(--fa-color-accent)}.fa-badge--success{background:var(--fa-color-success-soft);color:var(--fa-color-success)}.fa-badge--warning{background:var(--fa-color-warning-soft);color:var(--fa-color-warning)}.fa-badge--danger{background:var(--fa-color-danger-soft);color:var(--fa-color-danger)}.fa-button{justify-content:center;align-items:center;gap:var(--fa-space-2);min-height:2.25rem;padding:0 var(--fa-space-4);border-radius:var(--fa-radius);font:500 var(--fa-font-size-sm) / 1 var(--fa-font-sans);cursor:pointer;transition:background var(--fa-transition), border-color var(--fa-transition), color var(--fa-transition);border:1px solid #0000;display:inline-flex}.fa-button:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-button:disabled{cursor:not-allowed;opacity:.55}.fa-button--sm{min-height:1.75rem;padding:0 var(--fa-space-3);font-size:var(--fa-font-size-xs)}.fa-button--icon-only{width:2.25rem;padding:0}.fa-button--sm.fa-button--icon-only{width:1.75rem}.fa-button--primary{background:var(--fa-color-accent);color:var(--fa-color-accent-contrast)}.fa-button--primary:hover:not(:disabled){background:var(--fa-color-accent-hover)}.fa-button--secondary{background:var(--fa-color-surface);border-color:var(--fa-color-border);color:var(--fa-color-text)}.fa-button--secondary:hover:not(:disabled){border-color:var(--fa-color-border-strong)}.fa-button--ghost{color:var(--fa-color-text-muted);background:0 0}.fa-button--ghost:hover:not(:disabled),.fa-button--ghost[aria-pressed=true]{background:var(--fa-color-surface-sunken);color:var(--fa-color-text)}.fa-button--danger{background:var(--fa-color-danger);color:#fff}.fa-button--loading{cursor:progress}.fa-field{gap:var(--fa-space-1);font-family:var(--fa-font-sans);flex-direction:column;display:flex}.fa-field__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-field__input{min-height:2.25rem;padding:0 var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:var(--fa-font-size-sm) var(--fa-font-sans)}.fa-field__input:focus-visible{border-color:var(--fa-color-accent);box-shadow:var(--fa-focus-ring);outline:none}.fa-field__note{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);margin:0}.fa-field--error .fa-field__input{border-color:var(--fa-color-danger)}.fa-field--error .fa-field__note{color:var(--fa-color-danger)}.fa-dialog{z-index:1000;padding:var(--fa-space-4);background:var(--fa-color-overlay);font-family:var(--fa-font-sans);justify-content:center;align-items:center;display:flex;position:fixed;inset:0}.fa-dialog--side{justify-content:flex-end;align-items:stretch;padding:0}.fa-dialog__panel{width:100%;max-height:calc(100vh - 2 * var(--fa-space-4));background:var(--fa-color-surface);color:var(--fa-color-text);border-radius:var(--fa-radius-lg);box-shadow:var(--fa-shadow-lg);outline:none;flex-direction:column;display:flex}.fa-dialog__panel--sm{max-width:24rem}.fa-dialog__panel--md{max-width:34rem}.fa-dialog__panel--lg{max-width:52rem}.fa-dialog--side .fa-dialog__panel{border-radius:0;max-width:30rem;height:100%;max-height:none}.fa-dialog__header{justify-content:space-between;align-items:flex-start;gap:var(--fa-space-3);padding:var(--fa-space-4) var(--fa-space-4) var(--fa-space-3) var(--fa-space-5);border-bottom:1px solid var(--fa-color-border);display:flex}.fa-dialog__title{font-size:var(--fa-font-size-lg);margin:0;font-weight:600}.fa-dialog__description{margin:var(--fa-space-1) 0 0;font-size:var(--fa-font-size-sm);color:var(--fa-color-text-muted)}.fa-dialog__body{padding:var(--fa-space-4) var(--fa-space-5);flex:1;overflow-y:auto}.fa-dialog__footer{justify-content:flex-end;gap:var(--fa-space-2);padding:var(--fa-space-3) var(--fa-space-5);border-top:1px solid var(--fa-color-border);display:flex}.fa-table-wrap{border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);overflow-x:auto}.fa-table{border-collapse:collapse;width:100%;font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text)}.fa-table__caption{caption-side:top;text-align:start;padding:var(--fa-space-3) var(--fa-space-4);font-weight:600}.fa-table th,.fa-table td{padding:var(--fa-space-2) var(--fa-space-4);border-bottom:1px solid var(--fa-color-border)}.fa-table th{background:var(--fa-color-surface-raised);font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600}.fa-table tbody tr:last-child td{border-bottom:none}.fa-table--clickable tbody tr{cursor:pointer}.fa-table--clickable tbody tr:hover{background:var(--fa-color-surface-sunken)}.fa-table tbody tr:focus-visible{box-shadow:inset var(--fa-focus-ring);outline:none}.fa-table__cell--end{text-align:end;font-variant-numeric:tabular-nums}.fa-table__cell--center{text-align:center}.fa-table__sort{align-items:center;gap:var(--fa-space-1);color:inherit;font:inherit;text-transform:inherit;letter-spacing:inherit;cursor:pointer;background:0 0;border:0;padding:0;display:inline-flex}.fa-table__sort:focus-visible{box-shadow:var(--fa-focus-ring);border-radius:var(--fa-radius-sm);outline:none}.fa-table__empty{text-align:center;color:var(--fa-color-text-muted);padding:var(--fa-space-5)}.fa-synopsis{gap:var(--fa-space-4);color:var(--fa-color-text);font:var(--fa-font-size-md) / var(--fa-line-height) var(--fa-font-sans);flex-direction:column;display:flex}.fa-synopsis__rows{gap:var(--fa-space-3);flex-direction:column;display:flex}.fa-synopsis__state{padding:var(--fa-space-4);border:1px dashed var(--fa-color-border-strong);border-radius:var(--fa-radius);color:var(--fa-color-text-muted);text-align:center;margin:0}.fa-synopsis__state--error{border-style:solid;border-color:var(--fa-color-danger);background:var(--fa-color-danger-soft);color:var(--fa-color-danger)}.fa-synopsis-header{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-synopsis-header__title{font-size:var(--fa-font-size-lg);margin:0;line-height:1.3}.fa-synopsis-header p{margin:0}.fa-synopsis-header__files{overflow-wrap:anywhere;font-weight:600}.fa-synopsis-header__counts{color:var(--fa-color-text)}.fa-synopsis-header__meta{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-synopsis-header__hash{font-family:var(--fa-font-mono);overflow-wrap:anywhere}.fa-synopsis-header__commands{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius-sm);background:var(--fa-color-warning-soft);color:var(--fa-color-text);margin-top:var(--fa-space-2)!important}.fa-synopsis-header__notices{gap:var(--fa-space-2);margin:var(--fa-space-2) 0 0;flex-direction:column;padding:0;list-style:none;display:flex}.fa-synopsis-header__notices li{gap:var(--fa-space-2);padding:var(--fa-space-2) var(--fa-space-3);border-left:4px solid var(--fa-color-warning);border-radius:var(--fa-radius-sm);background:var(--fa-color-warning-soft);font-size:var(--fa-font-size-sm);align-items:flex-start;display:flex}.fa-synopsis-header__notices .fa-icon{color:var(--fa-color-warning);flex:none;margin-top:.15rem}.fa-synopsis-toolbar{gap:var(--fa-space-3);padding:var(--fa-space-3) var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface-raised);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);flex-direction:column;display:flex}.fa-synopsis-toolbar__row{align-items:center;gap:var(--fa-space-3) var(--fa-space-5);flex-wrap:wrap;display:flex}.fa-synopsis-toolbar__group,.fa-synopsis-toolbar__nav,.fa-synopsis-toolbar__export{align-items:center;gap:var(--fa-space-2);flex-wrap:wrap;display:inline-flex}.fa-synopsis-toolbar__search{flex:14rem;min-width:12rem}.fa-synopsis-toolbar__position{white-space:nowrap;text-overflow:ellipsis;width:16rem;color:var(--fa-color-text-muted);font-variant-numeric:tabular-nums;display:inline-block;overflow:hidden}.fa-synopsis-toolbar__filters{gap:var(--fa-space-2) var(--fa-space-4);border:0;flex-wrap:wrap;margin:0;padding:0;display:flex}.fa-synopsis-toolbar__filters legend{float:left;margin-right:var(--fa-space-3);color:var(--fa-color-text-muted);font-weight:600}.fa-synopsis-toolbar label{align-items:center;gap:var(--fa-space-1);cursor:pointer;display:inline-flex}.fa-synopsis-toolbar input[type=checkbox]{accent-color:var(--fa-color-accent);width:1rem;height:1rem}.fa-synopsis-toolbar input[type=checkbox]:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-synopsis-toolbar__options{gap:var(--fa-space-4);flex-wrap:wrap;display:inline-flex}.fa-synopsis-toolbar__label{color:var(--fa-color-text-muted);font-weight:600}.fa-synopsis-toolbar__export a{text-decoration:none}.fa-synopsis-toolbar__export a:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-synopsis-row{border:1px solid var(--fa-color-border);border-left:4px solid var(--fa-color-border-strong);border-radius:var(--fa-radius);background:var(--fa-color-surface);scroll-margin:var(--fa-space-6)}.fa-synopsis-row:focus-visible,.fa-synopsis-row--active{box-shadow:var(--fa-focus-ring);outline:none}.fa-synopsis-row--changed{border-left-color:var(--fa-color-accent)}.fa-synopsis-row--added{border-left-color:var(--fa-color-success)}.fa-synopsis-row--removed{border-left-color:var(--fa-color-danger)}.fa-synopsis-row--moved{border-left-color:var(--fa-color-warning)}.fa-synopsis-row--muted{opacity:.6}.fa-synopsis-row__head{align-items:center;gap:var(--fa-space-3);padding:var(--fa-space-2) var(--fa-space-4);border-bottom:1px solid var(--fa-color-border);background:var(--fa-color-surface-raised);border-radius:var(--fa-radius) var(--fa-radius) 0 0;flex-wrap:wrap;display:flex}.fa-synopsis-row__title{font-size:var(--fa-font-size-sm);flex:1;margin:0;font-weight:600}.fa-synopsis-row__include{align-items:center;gap:var(--fa-space-2);font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);display:inline-flex}.fa-synopsis-row__sides{grid-template-columns:1fr 1fr;display:grid}.fa-synopsis-row__side,.fa-synopsis-row__inline{padding:var(--fa-space-3) var(--fa-space-4);min-width:0}.fa-synopsis-row__side+.fa-synopsis-row__side{border-left:1px solid var(--fa-color-border)}.fa-synopsis-row__side-title{margin:0 0 var(--fa-space-2);font-size:var(--fa-font-size-xs);letter-spacing:.04em;text-transform:uppercase;color:var(--fa-color-text-muted);font-weight:600}.fa-synopsis-row__field{margin-top:var(--fa-space-3);font-size:var(--fa-font-size-sm)}.fa-synopsis-row__field strong{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);display:block}.fa-synopsis-row__reason{padding:var(--fa-space-2) var(--fa-space-4) var(--fa-space-3);border-top:1px dashed var(--fa-color-border);font-size:var(--fa-font-size-sm)}.fa-synopsis-row__reason p{white-space:pre-wrap;margin:0}.fa-synopsis-row__reason-edit{gap:var(--fa-space-1);font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);flex-direction:column;font-weight:600;display:flex}.fa-synopsis-row__reason-edit textarea{font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);background:var(--fa-color-surface);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-sm);padding:var(--fa-space-2);resize:vertical}.fa-synopsis-row__reason-edit textarea:focus-visible,.fa-synopsis-row__include input:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-synopsis-row__hint{font-size:var(--fa-font-size-xs);color:var(--fa-color-warning);margin-top:var(--fa-space-1)!important}.fa-synopsis-row__hint--ok{color:var(--fa-color-success)}@media (width<=720px){.fa-synopsis-row__sides{grid-template-columns:1fr}.fa-synopsis-row__side+.fa-synopsis-row__side{border-left:0;border-top:1px solid var(--fa-color-border)}}.fa-synopsis__text{white-space:pre-wrap;overflow-wrap:anywhere;margin:0;line-height:1.7}.fa-synopsis__empty{color:var(--fa-color-text-muted);font-style:italic}.fa-synopsis__del{background:var(--fa-color-danger-soft);color:var(--fa-color-danger);border-radius:2px;text-decoration:line-through;text-decoration-thickness:1.5px}.fa-synopsis__ins{background:var(--fa-color-success-soft);color:var(--fa-color-success);text-underline-offset:2px;border-radius:2px;text-decoration:underline;text-decoration-thickness:1.5px}.fa-synopsis-commands{padding:var(--fa-space-3) var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);font-size:var(--fa-font-size-sm)}.fa-synopsis-commands h3{margin:0 0 var(--fa-space-2);font-size:var(--fa-font-size-md)}.fa-synopsis-commands ol{padding-left:var(--fa-space-5);gap:var(--fa-space-1);flex-direction:column;margin:0;display:flex}.fa-synopsis-commands summary{cursor:pointer;font-weight:600}.fa-synopsis-commands summary:focus-visible{box-shadow:var(--fa-focus-ring);border-radius:var(--fa-radius-sm);outline:none}.fa-synopsis-commands dl{margin:var(--fa-space-3) 0 0}.fa-synopsis-commands dt{margin-top:var(--fa-space-2);font-weight:600}.fa-synopsis-commands dt span{color:var(--fa-color-text-muted);font-weight:400}.fa-synopsis-commands dd{white-space:pre-wrap;margin:0}.fa-synopsis-commands__repealed{color:var(--fa-color-text-muted);text-decoration:line-through}.fa-dataprotection{font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);box-sizing:border-box}.fa-dataprotection *,.fa-dataprotection :before,.fa-dataprotection :after{box-sizing:inherit}.fa-dataprotection h2{font-size:var(--fa-font-size-lg);margin:0}.fa-dataprotection h3{font-size:var(--fa-font-size-md);margin:0 0 var(--fa-space-2)}.fa-dataprotection h4{font-size:var(--fa-font-size-sm);margin:var(--fa-space-3) 0 var(--fa-space-2);color:var(--fa-color-text-muted);text-transform:uppercase;letter-spacing:.02em}.fa-dataprotection__header{justify-content:space-between;align-items:baseline;gap:var(--fa-space-3);margin-bottom:var(--fa-space-3);flex-wrap:wrap;display:flex}.fa-dataprotection__muted{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs)}.fa-dataprotection__panel{background:var(--fa-color-surface);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);padding:var(--fa-space-3) var(--fa-space-4);margin-bottom:var(--fa-space-4);min-width:0;box-shadow:var(--fa-shadow-sm)}.fa-dataprotection__bar{align-items:center;gap:var(--fa-space-2) var(--fa-space-3);flex-wrap:wrap;display:flex}.fa-dataprotection__actions{gap:var(--fa-space-2);flex-wrap:wrap;margin-left:auto;display:flex}.fa-dataprotection__alert{border-radius:var(--fa-radius-sm);padding:var(--fa-space-2) var(--fa-space-3);margin:0 0 var(--fa-space-3);background:var(--fa-color-danger-soft);color:var(--fa-color-danger)}.fa-dataprotection__alert--warning{background:var(--fa-color-warning-soft);color:var(--fa-color-warning)}.fa-dataprotection__alert--info{background:var(--fa-color-accent-soft);color:var(--fa-color-text)}.fa-dataprotection__live{min-height:1.2em;margin:0 0 var(--fa-space-2);color:var(--fa-color-success);font-size:var(--fa-font-size-xs)}.fa-dataprotection__table{border-collapse:collapse;width:100%}.fa-dataprotection__table th,.fa-dataprotection__table td{text-align:left;padding:var(--fa-space-1) var(--fa-space-2);border-bottom:1px solid var(--fa-color-border);vertical-align:top;overflow-wrap:anywhere}.fa-dataprotection__table th{color:var(--fa-color-text-muted);font-weight:600}.fa-dataprotection__field{gap:var(--fa-space-1);margin:0 0 var(--fa-space-3);border:0;min-width:0;padding:0;display:grid}.fa-dataprotection__field>label,.fa-dataprotection__field>legend,.fa-dataprotection__label{font-weight:600;font-size:var(--fa-font-size-sm);padding:0}.fa-dataprotection__field input:not([type=radio]):not([type=checkbox]),.fa-dataprotection__field select,.fa-dataprotection__field textarea{font:inherit;border:1px solid var(--fa-color-border-strong);border-radius:var(--fa-radius-sm);padding:var(--fa-space-1) var(--fa-space-2);background:var(--fa-color-surface);color:var(--fa-color-text);width:100%}.fa-dataprotection__field textarea{resize:vertical;min-height:3.5rem}.fa-dataprotection__field [aria-invalid=true]{border-color:var(--fa-color-danger)}.fa-dataprotection__field--required>label:after,.fa-dataprotection__field--required>legend:after{content:\" *\";color:var(--fa-color-danger)}.fa-dataprotection__ref{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs)}.fa-dataprotection__note{font-size:var(--fa-font-size-xs);color:var(--fa-color-warning);margin:0}.fa-dataprotection__note--blocking{color:var(--fa-color-danger)}.fa-dataprotection__choices{gap:var(--fa-space-1) var(--fa-space-3);flex-wrap:wrap;display:flex}.fa-dataprotection__choice{align-items:center;gap:var(--fa-space-1);cursor:pointer;display:inline-flex}.fa-dataprotection button:focus-visible,.fa-dataprotection input:focus-visible,.fa-dataprotection select:focus-visible,.fa-dataprotection textarea:focus-visible,.fa-dataprotection summary:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-dataprotection__chips{gap:var(--fa-space-1);margin:0 0 var(--fa-space-2);flex-wrap:wrap;padding:0;list-style:none;display:flex}.fa-dataprotection__chips li{align-items:center;gap:var(--fa-space-1);padding:0 0 0 var(--fa-space-2);background:var(--fa-color-surface-sunken);border-radius:999px;display:inline-flex}.fa-dataprotection__grid{gap:0 var(--fa-space-4);grid-template-columns:repeat(auto-fit,minmax(240px,1fr));display:grid}.fa-dataprotection__issues{padding-left:var(--fa-space-4);margin:0}.fa-dataprotection__issues li{margin:2px 0}.fa-dataprotection__issues .is-blocking{color:var(--fa-color-danger)}.fa-dataprotection__dl{gap:var(--fa-space-1) var(--fa-space-3);grid-template-columns:minmax(140px,32%) minmax(0,1fr);margin:0;display:grid}.fa-dataprotection__dl dt{color:var(--fa-color-text-muted);font-weight:600}.fa-dataprotection__dl dd{white-space:pre-wrap;overflow-wrap:anywhere;margin:0}.fa-vvt__layout{gap:var(--fa-space-4);grid-template-columns:minmax(240px,320px) minmax(0,1fr);align-items:start;display:grid}.fa-vvt__list{margin:0 0 var(--fa-space-3);padding:0;list-style:none}.fa-vvt__item{text-align:left;border:0;border-left:3px solid #0000;border-bottom:1px solid var(--fa-color-border);width:100%;padding:var(--fa-space-2);font:inherit;color:inherit;cursor:pointer;background:0 0;gap:2px;display:grid}.fa-vvt__item:hover{background:var(--fa-color-surface-sunken)}.fa-vvt__item[aria-current=true]{border-left-color:var(--fa-color-accent);background:var(--fa-color-accent-soft)}.fa-dsfa__tabs{gap:var(--fa-space-1);border-bottom:1px solid var(--fa-color-border);margin-bottom:var(--fa-space-3);flex-wrap:wrap;display:flex}.fa-dsfa__tab{font:inherit;padding:var(--fa-space-2) var(--fa-space-3);color:var(--fa-color-text-muted);cursor:pointer;background:0 0;border:0;border-bottom:2px solid #0000}.fa-dsfa__tab[aria-selected=true]{color:var(--fa-color-accent);border-bottom-color:var(--fa-color-accent);font-weight:600}.fa-dsfa__question{border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-sm);padding:var(--fa-space-2) var(--fa-space-3);margin:0 0 var(--fa-space-2)}.fa-dsfa__question legend{padding:0 var(--fa-space-1);font-weight:500}.fa-dsfa__question--yes{border-color:var(--fa-color-warning)}.fa-dsfa__meta{gap:var(--fa-space-2);margin:var(--fa-space-1) 0;flex-wrap:wrap;align-items:center;display:flex}.fa-dsfa__scenario{border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);padding:var(--fa-space-3);margin:0 0 var(--fa-space-3)}.fa-dsfa__measures{columns:2 260px;margin:0;padding:0;list-style:none}.fa-dsfa__measures li{break-inside:avoid;margin:2px 0}.fa-dsfa__result{gap:var(--fa-space-2);margin-top:var(--fa-space-2);flex-wrap:wrap;align-items:center;display:flex}@media (width<=860px){.fa-vvt__layout,.fa-dataprotection__dl{grid-template-columns:minmax(0,1fr)}}@media (prefers-reduced-motion:reduce){.fa-dataprotection *{transition:none!important}}.leaflet-pane,.leaflet-tile,.leaflet-marker-icon,.leaflet-marker-shadow,.leaflet-tile-container,.leaflet-pane>svg,.leaflet-pane>canvas,.leaflet-zoom-box,.leaflet-image-layer,.leaflet-layer{position:absolute;top:0;left:0}.leaflet-container{overflow:hidden}.leaflet-tile,.leaflet-marker-icon,.leaflet-marker-shadow{-webkit-user-select:none;user-select:none;-webkit-user-drag:none}.leaflet-tile::selection{background:0 0}.leaflet-safari .leaflet-tile{image-rendering:-webkit-optimize-contrast}.leaflet-safari .leaflet-tile-container{-webkit-transform-origin:0 0;width:1600px;height:1600px}.leaflet-marker-icon,.leaflet-marker-shadow{display:block}.leaflet-container .leaflet-overlay-pane svg{max-width:none!important;max-height:none!important}.leaflet-container .leaflet-marker-pane img,.leaflet-container .leaflet-shadow-pane img,.leaflet-container .leaflet-tile-pane img,.leaflet-container img.leaflet-image-layer,.leaflet-container .leaflet-tile{width:auto;padding:0;max-width:none!important;max-height:none!important}.leaflet-container img.leaflet-tile{mix-blend-mode:plus-lighter}.leaflet-container.leaflet-touch-zoom{-ms-touch-action:pan-x pan-y;touch-action:pan-x pan-y}.leaflet-container.leaflet-touch-drag{-ms-touch-action:pinch-zoom;touch-action:none;touch-action:pinch-zoom}.leaflet-container.leaflet-touch-drag.leaflet-touch-zoom{-ms-touch-action:none;touch-action:none}.leaflet-container{-webkit-tap-highlight-color:transparent}.leaflet-container a{-webkit-tap-highlight-color:#33b5e566}.leaflet-tile{filter:inherit;visibility:hidden}.leaflet-tile-loaded{visibility:inherit}.leaflet-zoom-box{box-sizing:border-box;z-index:800;width:0;height:0}.leaflet-overlay-pane svg{-moz-user-select:none}.leaflet-pane{z-index:400}.leaflet-tile-pane{z-index:200}.leaflet-overlay-pane{z-index:400}.leaflet-shadow-pane{z-index:500}.leaflet-marker-pane{z-index:600}.leaflet-tooltip-pane{z-index:650}.leaflet-popup-pane{z-index:700}.leaflet-map-pane canvas{z-index:100}.leaflet-map-pane svg{z-index:200}.leaflet-vml-shape{width:1px;height:1px}.lvml{behavior:url(#default#VML);display:inline-block;position:absolute}.leaflet-control{z-index:800;pointer-events:visiblePainted;pointer-events:auto;position:relative}.leaflet-top,.leaflet-bottom{z-index:1000;pointer-events:none;position:absolute}.leaflet-top{top:0}.leaflet-right{right:0}.leaflet-bottom{bottom:0}.leaflet-left{left:0}.leaflet-control{float:left;clear:both}.leaflet-right .leaflet-control{float:right}.leaflet-top .leaflet-control{margin-top:10px}.leaflet-bottom .leaflet-control{margin-bottom:10px}.leaflet-left .leaflet-control{margin-left:10px}.leaflet-right .leaflet-control{margin-right:10px}.leaflet-fade-anim .leaflet-popup{opacity:0;transition:opacity .2s linear}.leaflet-fade-anim .leaflet-map-pane .leaflet-popup{opacity:1}.leaflet-zoom-animated{transform-origin:0 0}svg.leaflet-zoom-animated{will-change:transform}.leaflet-zoom-anim .leaflet-zoom-animated{-webkit-transition:-webkit-transform .25s cubic-bezier(0,0,.25,1);-moz-transition:-moz-transform .25s cubic-bezier(0,0,.25,1);transition:transform .25s cubic-bezier(0,0,.25,1)}.leaflet-zoom-anim .leaflet-tile,.leaflet-pan-anim .leaflet-tile{transition:none}.leaflet-zoom-anim .leaflet-zoom-hide{visibility:hidden}.leaflet-interactive{cursor:pointer}.leaflet-grab{cursor:-webkit-grab;cursor:-moz-grab;cursor:grab}.leaflet-crosshair,.leaflet-crosshair .leaflet-interactive{cursor:crosshair}.leaflet-popup-pane,.leaflet-control{cursor:auto}.leaflet-dragging .leaflet-grab,.leaflet-dragging .leaflet-grab .leaflet-interactive,.leaflet-dragging .leaflet-marker-draggable{cursor:move;cursor:-webkit-grabbing;cursor:-moz-grabbing;cursor:grabbing}.leaflet-marker-icon,.leaflet-marker-shadow,.leaflet-image-layer,.leaflet-pane>svg path,.leaflet-tile-container{pointer-events:none}.leaflet-marker-icon.leaflet-interactive,.leaflet-image-layer.leaflet-interactive,.leaflet-pane>svg path.leaflet-interactive,svg.leaflet-image-layer.leaflet-interactive path{pointer-events:visiblePainted;pointer-events:auto}.leaflet-container{outline-offset:1px;background:#ddd}.leaflet-container a{color:#0078a8}.leaflet-zoom-box{background:#ffffff80;border:2px dotted #38f}.leaflet-container{font-family:Helvetica Neue,Arial,Helvetica,sans-serif;font-size:.75rem;line-height:1.5}.leaflet-bar{border-radius:4px;box-shadow:0 1px 5px #000000a6}.leaflet-bar a{text-align:center;color:#000;background-color:#fff;border-bottom:1px solid #ccc;width:26px;height:26px;line-height:26px;text-decoration:none;display:block}.leaflet-bar a,.leaflet-control-layers-toggle{background-position:50%;background-repeat:no-repeat;display:block}.leaflet-bar a:hover,.leaflet-bar a:focus{background-color:#f4f4f4}.leaflet-bar a:first-child{border-top-left-radius:4px;border-top-right-radius:4px}.leaflet-bar a:last-child{border-bottom:none;border-bottom-right-radius:4px;border-bottom-left-radius:4px}.leaflet-bar a.leaflet-disabled{cursor:default;color:#bbb;background-color:#f4f4f4}.leaflet-touch .leaflet-bar a{width:30px;height:30px;line-height:30px}.leaflet-touch .leaflet-bar a:first-child{border-top-left-radius:2px;border-top-right-radius:2px}.leaflet-touch .leaflet-bar a:last-child{border-bottom-right-radius:2px;border-bottom-left-radius:2px}.leaflet-control-zoom-in,.leaflet-control-zoom-out{text-indent:1px;font:700 18px Lucida Console,Monaco,monospace}.leaflet-touch .leaflet-control-zoom-in,.leaflet-touch .leaflet-control-zoom-out{font-size:22px}.leaflet-control-layers{background:#fff;border-radius:5px;box-shadow:0 1px 5px #0006}.leaflet-control-layers-toggle{background-image:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABoAAAAaCAQAAAADQ4RFAAACf0lEQVR4AY1UM3gkARTePdvdoTxXKc+qTl3aU5U6b2Kbkz3Gtq3Zw6ziLGNPzrYx7946Tr6/ee/XeCQ4D3ykPtL5tHno4n0d/h3+xfuWHGLX81cn7r0iTNzjr7LrlxCqPtkbTQEHeqOrTy4Yyt3VCi/IOB0v7rVC7q45Q3Gr5K6jt+3Gl5nCoDD4MtO+j96Wu8atmhGqcNGHObuf8OM/x3AMx38+4Z2sPqzCxRFK2aF2e5Jol56XTLyggAMTL56XOMoS1W4pOyjUcGGQdZxU6qRh7B9Zp+PfpOFlqt0zyDZckPi1ttmIp03jX8gyJ8a/PG2yutpS/Vol7peZIbZcKBAEEheEIAgFbDkz5H6Zrkm2hVWGiXKiF4Ycw0RWKdtC16Q7qe3X4iOMxruonzegJzWaXFrU9utOSsLUmrc0YjeWYjCW4PDMADElpJSSQ0vQvA1Tm6/JlKnqFs1EGyZiFCqnRZTEJJJiKRYzVYzJck2Rm6P4iH+cmSY0YzimYa8l0EtTODFWhcMIMVqdsI2uiTvKmTisIDHJ3od5GILVhBCarCfVRmo4uTjkhrhzkiBV7SsaqS+TzrzM1qpGGUFt28pIySQHR6h7F6KSwGWm97ay+Z+ZqMcEjEWebE7wxCSQwpkhJqoZA5ivCdZDjJepuJ9IQjGGUmuXJdBFUygxVqVsxFsLMbDe8ZbDYVCGKxs+W080max1hFCarCfV+C1KATwcnvE9gRRuMP2prdbWGowm1KB1y+zwMMENkM755cJ2yPDtqhTI6ED1M/82yIDtC/4j4BijjeObflpO9I9MwXTCsSX8jWAFeHr05WoLTJ5G8IQVS/7vwR6ohirYM7f6HzYpogfS3R2OAAAAAElFTkSuQmCC);width:36px;height:36px}.leaflet-retina .leaflet-control-layers-toggle{background-image:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADQAAAA0CAQAAABvcdNgAAAEsklEQVR4AWL4TydIhpZK1kpWOlg0w3ZXP6D2soBtG42jeI6ZmQTHzAxiTbSJsYLjO9HhP+WOmcuhciVnmHVQcJnp7DFvScowZorad/+V/fVzMdMT2g9Cv9guXGv/7pYOrXh2U+RRR3dSd9JRx6bIFc/ekqHI29JC6pJ5ZEh1yWkhkbcFeSjxgx3L2m1cb1C7bceyxA+CNjT/Ifff+/kDk2u/w/33/IeCMOSaWZ4glosqT3DNnNZQ7Cs58/3Ce5HL78iZH/vKVIaYlqzfdLu8Vi7dnvUbEza5Idt36tquZFldl6N5Z/POLof0XLK61mZCmJSWjVF9tEjUluu74IUXvgttuVIHE7YxSkaYhJZam7yiM9Pv82JYfl9nptxZaxMJE4YSPty+vF0+Y2up9d3wwijfjZbabqm/3bZ9ecKHsiGmRflnn1MW4pjHf9oLufyn2z3y1D6n8g8TZhxyzipLNPnAUpsOiuWimg52psrTZYnOWYNDTMuWBWa0tJb4rgq1UvmutpaYEbZlwU3CLJm/ayYjHW5/h7xWLn9Hh1vepDkyf7dE7MtT5LR4e7yYpHrkhOUpEfssBLq2pPhAqoSWKUkk7EDqkmK6RrCEzqDjhNDWNE+XSMvkJRDWlZTmCW0l0PHQGRZY5t1L83kT0Y3l2SItk5JAWHl2dCOBm+fPu3fo5/3v61RMCO9Jx2EEYYhb0rmNQMX/vm7gqOEJLcXTGw3CAuRNeyaPWwjR8PRqKQ1PDA/dpv+on9Shox52WFnx0KY8onHayrJzm87i5h9xGw/tfkev0jGsQizqezUKjk12hBMKJ4kbCqGPVNXudyyrShovGw5CgxsRICxF6aRmSjlBnHRzg7Gx8fKqEubI2rahQYdR1YgDIRQO7JvQyD52hoIQx0mxa0ODtW2Iozn1le2iIRdzwWewedyZzewidueOGqlsn1MvcnQpuVwLGG3/IR1hIKxCjelIDZ8ldqWz25jWAsnldEnK0Zxro19TGVb2ffIZEsIO89EIEDvKMPrzmBOQcKQ+rroye6NgRRxqR4U8EAkz0CL6uSGOm6KQCdWjvjRiSP1BPalCRS5iQYiEIvxuBMJEWgzSoHADcVMuN7IuqqTeyUPq22qFimFtxDyBBJEwNyt6TM88blFHao/6tWWhuuOM4SAK4EI4QmFHA+SEyWlp4EQoJ13cYGzMu7yszEIBOm2rVmHUNqwAIQabISNMRstmdhNWcFLsSm+0tjJH1MdRxO5Nx0WDMhCtgD6OKgZeljJqJKc9po8juskR9XN0Y1lZ3mWjLR9JCO1jRDMd0fpYC2VnvjBSEFg7wBENc0R9HFlb0xvF1+TBEpF68d+DHR6IOWVv2BECtxo46hOFUBd/APU57WIoEwJhIi2CdpyZX0m93BZicktMj1AS9dClteUFAUNUIEygRZCtik5zSxI9MubTBH1GOiHsiLJ3OCoSZkILa9PxiN0EbvhsAo8tdAf9Seepd36lGWHmtNANTv5Jd0z4QYyeo/UEJqxKRpg5LZx6btLPsOaEmdMyxYdlc8LMaJnikDlhclqmPiQnTEpLUIZEwkRagjYkEibQErwhkTAKCLQEbUgkzJQWc/0PstHHcfEdQ+UAAAAASUVORK5CYII=);background-size:26px 26px}.leaflet-touch .leaflet-control-layers-toggle{width:44px;height:44px}.leaflet-control-layers .leaflet-control-layers-list,.leaflet-control-layers-expanded .leaflet-control-layers-toggle{display:none}.leaflet-control-layers-expanded .leaflet-control-layers-list{display:block;position:relative}.leaflet-control-layers-expanded{color:#333;background:#fff;padding:6px 10px 6px 6px}.leaflet-control-layers-scrollbar{padding-right:5px;overflow:hidden scroll}.leaflet-control-layers-selector{margin-top:2px;position:relative;top:1px}.leaflet-control-layers label{font-size:1.08333em;display:block}.leaflet-control-layers-separator{border-top:1px solid #ddd;height:0;margin:5px -10px 5px -6px}.leaflet-default-icon-path{background-image:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABkAAAApCAYAAADAk4LOAAAFgUlEQVR4Aa1XA5BjWRTN2oW17d3YaZtr2962HUzbDNpjszW24mRt28p47v7zq/bXZtrp/lWnXr337j3nPCe85NcypgSFdugCpW5YoDAMRaIMqRi6aKq5E3YqDQO3qAwjVWrD8Ncq/RBpykd8oZUb/kaJutow8r1aP9II0WmLKLIsJyv1w/kqw9Ch2MYdB++12Onxee/QMwvf4/Dk/Lfp/i4nxTXtOoQ4pW5Aj7wpici1A9erdAN2OH64x8OSP9j3Ft3b7aWkTg/Fm91siTra0f9on5sQr9INejH6CUUUpavjFNq1B+Oadhxmnfa8RfEmN8VNAsQhPqF55xHkMzz3jSmChWU6f7/XZKNH+9+hBLOHYozuKQPxyMPUKkrX/K0uWnfFaJGS1QPRtZsOPtr3NsW0uyh6NNCOkU3Yz+bXbT3I8G3xE5EXLXtCXbbqwCO9zPQYPRTZ5vIDXD7U+w7rFDEoUUf7ibHIR4y6bLVPXrz8JVZEql13trxwue/uDivd3fkWRbS6/IA2bID4uk0UpF1N8qLlbBlXs4Ee7HLTfV1j54APvODnSfOWBqtKVvjgLKzF5YdEk5ewRkGlK0i33Eofffc7HT56jD7/6U+qH3Cx7SBLNntH5YIPvODnyfIXZYRVDPqgHtLs5ABHD3YzLuespb7t79FY34DjMwrVrcTuwlT55YMPvOBnRrJ4VXTdNnYug5ucHLBjEpt30701A3Ts+HEa73u6dT3FNWwflY86eMHPk+Yu+i6pzUpRrW7SNDg5JHR4KapmM5Wv2E8Tfcb1HoqqHMHU+uWDD7zg54mz5/2BSnizi9T1Dg4QQXLToGNCkb6tb1NU+QAlGr1++eADrzhn/u8Q2YZhQVlZ5+CAOtqfbhmaUCS1ezNFVm2imDbPmPng5wmz+gwh+oHDce0eUtQ6OGDIyR0uUhUsoO3vfDmmgOezH0mZN59x7MBi++WDL1g/eEiU3avlidO671bkLfwbw5XV2P8Pzo0ydy4t2/0eu33xYSOMOD8hTf4CrBtGMSoXfPLchX+J0ruSePw3LZeK0juPJbYzrhkH0io7B3k164hiGvawhOKMLkrQLyVpZg8rHFW7E2uHOL888IBPlNZ1FPzstSJM694fWr6RwpvcJK60+0HCILTBzZLFNdtAzJaohze60T8qBzyh5ZuOg5e7uwQppofEmf2++DYvmySqGBuKaicF1blQjhuHdvCIMvp8whTTfZzI7RldpwtSzL+F1+wkdZ2TBOW2gIF88PBTzD/gpeREAMEbxnJcaJHNHrpzji0gQCS6hdkEeYt9DF/2qPcEC8RM28Hwmr3sdNyht00byAut2k3gufWNtgtOEOFGUwcXWNDbdNbpgBGxEvKkOQsxivJx33iow0Vw5S6SVTrpVq11ysA2Rp7gTfPfktc6zhtXBBC+adRLshf6sG2RfHPZ5EAc4sVZ83yCN00Fk/4kggu40ZTvIEm5g24qtU4KjBrx/BTTH8ifVASAG7gKrnWxJDcU7x8X6Ecczhm3o6YicvsLXWfh3Ch1W0k8x0nXF+0fFxgt4phz8QvypiwCCFKMqXCnqXExjq10beH+UUA7+nG6mdG/Pu0f3LgFcGrl2s0kNNjpmoJ9o4B29CMO8dMT4Q5ox8uitF6fqsrJOr8qnwNbRzv6hSnG5wP+64C7h9lp30hKNtKdWjtdkbuPA19nJ7Tz3zR/ibgARbhb4AlhavcBebmTHcFl2fvYEnW0ox9xMxKBS8btJ+KiEbq9zA4RthQXDhPa0T9TEe69gWupwc6uBUphquXgf+/FrIjweHQS4/pduMe5ERUMHUd9xv8ZR98CxkS4F2n3EUrUZ10EYNw7BWm9x1GiPssi3GgiGRDKWRYZfXlON+dfNbM+GgIwYdwAAAAASUVORK5CYII=)}.leaflet-container .leaflet-control-attribution{background:#fffc;margin:0}.leaflet-control-attribution,.leaflet-control-scale-line{color:#333;padding:0 5px;line-height:1.4}.leaflet-control-attribution a{text-decoration:none}.leaflet-control-attribution a:hover,.leaflet-control-attribution a:focus{text-decoration:underline}.leaflet-attribution-flag{width:1em;height:.6669em;vertical-align:baseline!important;display:inline!important}.leaflet-left .leaflet-control-scale{margin-left:5px}.leaflet-bottom .leaflet-control-scale{margin-bottom:5px}.leaflet-control-scale-line{white-space:nowrap;box-sizing:border-box;text-shadow:1px 1px #fff;background:#fffc;border:2px solid #777;border-top:none;padding:2px 5px 1px;line-height:1.1}.leaflet-control-scale-line:not(:first-child){border-top:2px solid #777;border-bottom:none;margin-top:-2px}.leaflet-control-scale-line:not(:first-child):not(:last-child){border-bottom:2px solid #777}.leaflet-touch .leaflet-control-attribution,.leaflet-touch .leaflet-control-layers,.leaflet-touch .leaflet-bar{box-shadow:none}.leaflet-touch .leaflet-control-layers,.leaflet-touch .leaflet-bar{background-clip:padding-box;border:2px solid #0003}.leaflet-popup{text-align:center;margin-bottom:20px;position:absolute}.leaflet-popup-content-wrapper{text-align:left;border-radius:12px;padding:1px}.leaflet-popup-content{min-height:1px;margin:13px 24px 13px 20px;font-size:1.08333em;line-height:1.3}.leaflet-popup-content p{margin:1.3em 0}.leaflet-popup-tip-container{pointer-events:none;width:40px;height:20px;margin-top:-1px;margin-left:-20px;position:absolute;left:50%;overflow:hidden}.leaflet-popup-tip{pointer-events:auto;width:17px;height:17px;margin:-10px auto 0;padding:1px;transform:rotate(45deg)}.leaflet-popup-content-wrapper,.leaflet-popup-tip{color:#333;background:#fff;box-shadow:0 3px 14px #0006}.leaflet-container a.leaflet-popup-close-button{text-align:center;color:#757575;background:0 0;border:none;width:24px;height:24px;font:16px/24px Tahoma,Verdana,sans-serif;text-decoration:none;position:absolute;top:0;right:0}.leaflet-container a.leaflet-popup-close-button:hover,.leaflet-container a.leaflet-popup-close-button:focus{color:#585858}.leaflet-popup-scrolled{overflow:auto}.leaflet-oldie .leaflet-popup-content-wrapper{-ms-zoom:1}.leaflet-oldie .leaflet-popup-tip{-ms-filter:\"progid:DXImageTransform.Microsoft.Matrix(M11=0.70710678, M12=0.70710678, M21=-0.70710678, M22=0.70710678)\";width:24px;filter:progid:DXImageTransform.Microsoft.Matrix(M11=.707107, M12=.707107, M21=-.707107, M22=.707107);margin:0 auto}.leaflet-oldie .leaflet-control-zoom,.leaflet-oldie .leaflet-control-layers,.leaflet-oldie .leaflet-popup-content-wrapper,.leaflet-oldie .leaflet-popup-tip{border:1px solid #999}.leaflet-div-icon{background:#fff;border:1px solid #666}.leaflet-tooltip{color:#222;white-space:nowrap;-webkit-user-select:none;user-select:none;pointer-events:none;background-color:#fff;border:1px solid #fff;border-radius:3px;padding:6px;position:absolute;box-shadow:0 1px 3px #0006}.leaflet-tooltip.leaflet-interactive{cursor:pointer;pointer-events:auto}.leaflet-tooltip-top:before,.leaflet-tooltip-bottom:before,.leaflet-tooltip-left:before,.leaflet-tooltip-right:before{pointer-events:none;content:\"\";background:0 0;border:6px solid #0000;position:absolute}.leaflet-tooltip-bottom{margin-top:6px}.leaflet-tooltip-top{margin-top:-6px}.leaflet-tooltip-bottom:before,.leaflet-tooltip-top:before{margin-left:-6px;left:50%}.leaflet-tooltip-top:before{border-top-color:#fff;margin-bottom:-12px;bottom:0}.leaflet-tooltip-bottom:before{border-bottom-color:#fff;margin-top:-12px;margin-left:-6px;top:0}.leaflet-tooltip-left{margin-left:-6px}.leaflet-tooltip-right{margin-left:6px}.leaflet-tooltip-left:before,.leaflet-tooltip-right:before{margin-top:-6px;top:50%}.leaflet-tooltip-left:before{border-left-color:#fff;margin-right:-12px;right:0}.leaflet-tooltip-right:before{border-right-color:#fff;margin-left:-12px;left:0}@media print{.leaflet-control{-webkit-print-color-adjust:exact;print-color-adjust:exact}}.fa-geo{gap:var(--fa-space-3);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-geo__layout{gap:var(--fa-space-4);grid-template-columns:minmax(18rem,1fr) minmax(18rem,24rem);align-items:start;display:grid}@media (width<=52rem){.fa-geo__layout{grid-template-columns:1fr}}.fa-geo__canvas-wrap{gap:var(--fa-space-2);min-width:0;top:var(--fa-space-3);flex-direction:column;display:flex;position:sticky}.fa-geo__canvas{border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-lg);background:var(--fa-color-surface-sunken);height:min(70vh,36rem);min-height:20rem;overflow:hidden}.fa-geo__canvas:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-geo__map-bar{gap:var(--fa-space-2);flex-wrap:wrap;justify-content:space-between;align-items:center;display:flex}.fa-geo__panel{gap:var(--fa-space-3);flex-direction:column;min-width:0;display:flex}.fa-geo__card{gap:var(--fa-space-2);padding:var(--fa-space-3) var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-lg);background:var(--fa-color-surface);box-shadow:var(--fa-shadow-sm);flex-direction:column;display:flex}.fa-geo__heading{font-size:var(--fa-font-size-md);margin:0;font-weight:600}.fa-geo__row{gap:var(--fa-space-2);flex-wrap:wrap;align-items:flex-end;display:flex}.fa-geo__stack{gap:var(--fa-space-2);flex-direction:column;display:flex}.fa-geo__row>.fa-geo__grow{flex:10rem}.fa-geo__field{gap:var(--fa-space-1);flex-direction:column;min-width:0;display:flex}.fa-geo__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-geo__input{width:100%;min-width:6.5rem;min-height:2.25rem;padding:0 var(--fa-space-2);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit;box-sizing:border-box}.fa-geo__input--short{width:4.5rem;min-width:4rem}.fa-geo__utm summary{cursor:pointer;font-weight:600}.fa-geo__utm[open] summary{margin-bottom:var(--fa-space-2)}.fa-geo__input[aria-invalid=true]{border-color:var(--fa-color-danger)}.fa-geo__input:focus-visible,.fa-geo__range:focus-visible,.fa-geo__check input:focus-visible,.fa-geo__file:focus-visible,.fa-geo__link:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-geo__range{width:100%;accent-color:var(--fa-color-accent)}.fa-geo__check{gap:var(--fa-space-2);align-items:center;display:inline-flex}.fa-geo__fieldset{gap:var(--fa-space-3);padding:var(--fa-space-1) var(--fa-space-3) var(--fa-space-2);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);flex-wrap:wrap;margin:0;display:flex}.fa-geo__muted{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs);margin:0}.fa-geo__summary{gap:var(--fa-space-2);flex-wrap:wrap;align-items:center;margin:0;display:flex}.fa-geo__error{font-size:var(--fa-font-size-xs);color:var(--fa-color-danger);margin:0}.fa-geo__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-geo__notice{padding:var(--fa-space-2) var(--fa-space-3);border-left:3px solid var(--fa-color-warning);background:var(--fa-color-warning-soft);border-radius:var(--fa-radius-sm);margin:0}.fa-geo__facts{gap:var(--fa-space-1) var(--fa-space-3);grid-template-columns:max-content 1fr;margin:0;display:grid}.fa-geo__facts dt{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-geo__facts dd{font-variant-numeric:tabular-nums;overflow-wrap:anywhere;margin:0}.fa-geo__table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%}.fa-geo__table th,.fa-geo__table td{padding:var(--fa-space-1) var(--fa-space-2);border-bottom:1px solid var(--fa-color-border);text-align:left}.fa-geo__table th{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-geo__num{white-space:nowrap;text-align:right!important}.fa-geo__list{padding-left:var(--fa-space-4);margin:0}.fa-geo__link{color:var(--fa-color-accent);font:inherit;text-align:left;cursor:pointer;background:0 0;border:0;padding:0;text-decoration:underline}.fa-geo__details summary{cursor:pointer;font-weight:600}.fa-geo .leaflet-container{font:inherit;background:var(--fa-color-surface-sunken)}.fa-geo .leaflet-control-attribution{font-size:var(--fa-font-size-xs)}.fa-geo__area{stroke:var(--fa-color-accent);stroke-width:2px;fill:var(--fa-color-accent);fill-opacity:.12}.fa-geo__area--selected{stroke-width:3px;fill-opacity:.25}.fa-geo__simplified{stroke:var(--fa-color-warning);stroke-width:2px;stroke-dasharray:6 4;fill:none}.fa-geo__point{stroke:var(--fa-color-surface);stroke-width:1.5px;fill:var(--fa-color-text-muted);fill-opacity:.9}.fa-geo__point--hit{fill:var(--fa-color-success)}.fa-geo__radius{stroke:var(--fa-color-success);stroke-width:1.5px;stroke-dasharray:4 3;fill:var(--fa-color-success);fill-opacity:.06}.fa-geo__reference{stroke:var(--fa-color-surface);stroke-width:2px;fill:var(--fa-color-danger);fill-opacity:1}@media (prefers-reduced-motion:reduce){.fa-geo .leaflet-zoom-anim .leaflet-zoom-animated{transition:none!important}}.fa-risk{gap:var(--fa-space-4);font-family:var(--fa-font-sans);color:var(--fa-color-text);display:grid}.fa-risk__head h2{font-size:var(--fa-font-size-lg);margin:0}.fa-risk__profile{margin:var(--fa-space-1) 0 0;font-size:var(--fa-font-size-sm);color:var(--fa-color-text-muted)}.fa-risk__hint{margin:var(--fa-space-2) 0 0;padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius-sm);background:var(--fa-color-warning-soft);color:var(--fa-color-warning);font-size:var(--fa-font-size-sm);font-weight:600}.fa-risk__body{gap:var(--fa-space-4);align-items:start;display:grid}@media (width>=72rem){.fa-risk__body{grid-template-columns:minmax(0,1fr) minmax(22rem,30rem)}}.fa-risk__profile-info summary{cursor:pointer;color:var(--fa-color-accent);padding:var(--fa-space-2) 0;font-weight:600}.fa-risk__profile-info summary:focus-visible{box-shadow:var(--fa-focus-ring);border-radius:var(--fa-radius-sm);outline:none}@media (prefers-reduced-motion:reduce){.fa-risk *{transition:none!important}}.fa-risk-summary{gap:var(--fa-space-3);display:grid}.fa-risk-summary__totals{gap:var(--fa-space-4);font-size:var(--fa-font-size-sm);color:var(--fa-color-text);flex-wrap:wrap;margin:0;padding:0;list-style:none;display:flex}.fa-risk-summary__totals li{align-items:center;gap:var(--fa-space-1);display:inline-flex}.fa-risk-summary__code{color:var(--fa-color-accent);font:600 var(--fa-font-size-sm) var(--fa-font-mono);cursor:pointer;background:0 0;border:0;padding:0;-webkit-text-decoration:underline dotted;text-decoration:underline dotted}.fa-risk-summary__code:focus-visible{box-shadow:var(--fa-focus-ring);border-radius:var(--fa-radius-sm);outline:none}.fa-risk-summary__skipped{margin-top:var(--fa-space-1);font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);display:block}.fa-risk-summary__count{align-items:center;gap:var(--fa-space-1);white-space:nowrap;display:inline-flex}.fa-risk-summary__bar{width:4rem;height:.4rem;background:var(--fa-color-surface-sunken);vertical-align:middle;border-radius:999px;margin-inline-end:var(--fa-space-2);display:inline-block;overflow:hidden}.fa-risk-summary__bar span{background:var(--fa-color-danger);height:100%;display:block}.fa-risk-summary__undetermined{justify-items:end;gap:2px;display:inline-grid}.fa-risk-summary__undetermined small{font-size:var(--fa-font-size-xs);color:var(--fa-color-warning)}.fa-risk-summary__dataset h3{margin:0 0 var(--fa-space-2);font-size:var(--fa-font-size-md)}.fa-risk-summary__dataset p{font-size:var(--fa-font-size-sm);margin:0}.fa-risk-filter{gap:var(--fa-space-2) var(--fa-space-3);font-size:var(--fa-font-size-sm);color:var(--fa-color-text);grid-template-columns:auto minmax(10rem,1fr);align-items:center;display:grid}.fa-risk-filter label{color:var(--fa-color-text-muted);font-weight:600}.fa-risk-filter select,.fa-risk-filter input{min-width:0;padding:var(--fa-space-1) var(--fa-space-2);border:1px solid var(--fa-color-border-strong);border-radius:var(--fa-radius-sm);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit}.fa-risk-filter select:focus-visible,.fa-risk-filter input:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-risk-filter__result{color:var(--fa-color-text-muted);grid-column:1/-1}@media (width>=60rem){.fa-risk-filter{grid-template-columns:auto minmax(12rem,1fr) auto minmax(10rem,14rem) auto minmax(10rem,1fr)}}.fa-risk-table .fa-table td{padding-block:var(--fa-space-1)}.fa-risk-table__record{font-family:var(--fa-font-mono);font-size:var(--fa-font-size-sm)}.fa-risk-table__record[aria-current=true]{color:var(--fa-color-accent);font-weight:700}.fa-risk-table__record[aria-current=true]:before{content:\"▸ \"}.fa-risk-state{align-items:center;gap:var(--fa-space-1);padding:.0625rem var(--fa-space-2);font:600 var(--fa-font-size-xs) / 1.3 var(--fa-font-sans);white-space:nowrap;border:1px solid #0000;border-radius:999px;display:inline-flex}.fa-risk-state__icon{place-items:center;width:1.1em;height:1.1em;font-weight:700;display:inline-grid}.fa-risk-state--compact{justify-content:center;min-width:1.6em;padding:.0625rem}.fa-risk-state--danger{background:var(--fa-color-danger-soft);color:var(--fa-color-danger);border-color:var(--fa-color-danger)}.fa-risk-state--warning{background:var(--fa-color-warning-soft);color:var(--fa-color-warning);border:1px dashed var(--fa-color-warning)}.fa-risk-state--neutral{color:var(--fa-color-text-muted)}.fa-risk-state--skipped{border:1px dotted var(--fa-color-border-strong)}.fa-risk-detail{gap:var(--fa-space-3);align-content:start;display:grid}.fa-risk-detail h3{font-size:var(--fa-font-size-lg);color:var(--fa-color-text);margin:0}.fa-risk-detail__empty{padding:var(--fa-space-4);border:1px dashed var(--fa-color-border-strong);border-radius:var(--fa-radius);color:var(--fa-color-text-muted);font-size:var(--fa-font-size-sm);margin:0}.fa-risk-detail__assessment{gap:2px var(--fa-space-3);font-size:var(--fa-font-size-sm);grid-template-columns:max-content 1fr;margin:0;display:grid}.fa-risk-detail__assessment dt{color:var(--fa-color-text-muted)}.fa-risk-detail__assessment dd{margin:0}.fa-risk-card{gap:var(--fa-space-2);padding:var(--fa-space-3) var(--fa-space-4);border:1px solid var(--fa-color-border);border-inline-start:4px solid var(--fa-color-danger);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);display:grid}.fa-risk-card--undetermined{border-style:dashed;border-inline-start:4px dashed var(--fa-color-warning);background:var(--fa-color-surface-raised)}.fa-risk-card__head{align-items:center;gap:var(--fa-space-2);flex-wrap:wrap;display:flex}.fa-risk-card__head h4{font-size:var(--fa-font-size-md);flex:16rem;margin:0}.fa-risk-card code{font-family:var(--fa-font-mono);font-size:.95em}.fa-risk-card__profile{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);margin:0}.fa-risk-card__reason,.fa-risk-card__note{margin:0}.fa-risk-card__note{color:var(--fa-color-text-muted)}.fa-risk-card__grid{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));display:grid}.fa-risk-card__pairs{border-collapse:collapse;width:100%}.fa-risk-card__pairs caption{text-align:start;padding-bottom:var(--fa-space-1);font-weight:600}.fa-risk-card__pairs th,.fa-risk-card__pairs td{padding:2px var(--fa-space-2);border-bottom:1px solid var(--fa-color-border);text-align:start;vertical-align:top}.fa-risk-card__pairs thead th{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-risk-card__pairs tbody th{color:var(--fa-color-text-muted);font-weight:400}.fa-risk-card__empty{color:var(--fa-color-warning);font-style:italic;font-weight:600}.fa-risk-card__more summary{cursor:pointer;color:var(--fa-color-accent)}.fa-risk-card__more summary:focus-visible{box-shadow:var(--fa-focus-ring);border-radius:var(--fa-radius-sm);outline:none}.fa-risk-card__more dl{gap:2px var(--fa-space-3);margin:var(--fa-space-2) 0 0;grid-template-columns:max-content 1fr;display:grid}.fa-risk-card__more dt{color:var(--fa-color-text-muted)}.fa-risk-card__more dd{word-break:break-word;margin:0}.fa-risk-profile{gap:var(--fa-space-3);font-size:var(--fa-font-size-sm);color:var(--fa-color-text);display:grid}.fa-risk-profile__identity{gap:var(--fa-space-1) var(--fa-space-3);grid-template-columns:max-content 1fr;margin:0;display:grid}.fa-risk-profile__identity dt{color:var(--fa-color-text-muted);font-weight:600}.fa-risk-profile__identity dd{min-width:0;margin:0}.fa-risk-profile__hash{word-break:break-all;font-size:var(--fa-font-size-xs)}.fa-risk-profile__hint{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius-sm);background:var(--fa-color-warning-soft);color:var(--fa-color-warning);margin:0;font-weight:600}.fa-risk-profile__legal{color:var(--fa-color-text-muted);margin:0}.fa-risk-profile h4{margin:0 0 var(--fa-space-1)}.fa-risk-profile__chip{margin:0 var(--fa-space-1) 2px 0;padding:0 var(--fa-space-1);border-radius:var(--fa-radius-sm);background:var(--fa-color-surface-sunken);font-family:var(--fa-font-mono);font-size:var(--fa-font-size-xs);display:inline-block}.fa-risk-profile__param,.fa-risk-profile__use{font-size:var(--fa-font-size-xs);display:block}.fa-screening{font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);box-sizing:border-box}.fa-screening *,.fa-screening :before,.fa-screening :after{box-sizing:inherit}.fa-screening h2{font-size:var(--fa-font-size-lg);margin:0}.fa-screening h3{justify-content:space-between;align-items:baseline;gap:var(--fa-space-2);font-size:var(--fa-font-size-md);margin:0 0 var(--fa-space-2);flex-wrap:wrap;display:flex}.fa-screening__header{justify-content:space-between;align-items:baseline;gap:var(--fa-space-3);margin-bottom:var(--fa-space-3);flex-wrap:wrap;display:flex}.fa-screening__notice,.fa-screening__muted{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs)}.fa-screening__notice{font-size:var(--fa-font-size-sm)}.fa-screening__layout{gap:var(--fa-space-4);grid-template-columns:minmax(260px,320px) minmax(0,1fr);align-items:start;display:grid}.fa-screening__main{gap:var(--fa-space-4);grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);align-items:start;display:grid}.fa-screening__panel{background:var(--fa-color-surface);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);padding:var(--fa-space-3) var(--fa-space-4);margin-bottom:var(--fa-space-4);min-width:0;box-shadow:var(--fa-shadow-sm)}.fa-screening__table{border-collapse:collapse;width:100%;font-size:var(--fa-font-size-sm)}.fa-screening__table th,.fa-screening__table td{text-align:left;padding:var(--fa-space-1) var(--fa-space-2);border-bottom:1px solid var(--fa-color-border);vertical-align:top;overflow-wrap:anywhere}.fa-screening__table th{color:var(--fa-color-text-muted);font-weight:600}.fa-screening__table a{color:var(--fa-color-accent)}.fa-screening__btn{font:inherit;border:1px solid var(--fa-color-border-strong);background:var(--fa-color-surface);color:var(--fa-color-text);border-radius:var(--fa-radius-sm);padding:var(--fa-space-1) var(--fa-space-3);cursor:pointer;transition:border-color var(--fa-transition), background var(--fa-transition)}.fa-screening__btn:hover:not(:disabled){border-color:var(--fa-color-accent)}.fa-screening__btn:disabled{opacity:.55;cursor:not-allowed}.fa-screening__btn--primary{background:var(--fa-color-accent);border-color:var(--fa-color-accent);color:var(--fa-color-accent-contrast)}.fa-screening__btn--primary:hover:not(:disabled){background:var(--fa-color-accent-hover)}.fa-screening__btn--confirmed{border-color:var(--fa-color-danger);color:var(--fa-color-danger)}.fa-screening__btn--dismissed{border-color:var(--fa-color-success);color:var(--fa-color-success)}.fa-screening__btn[aria-pressed=true]{font-weight:600;box-shadow:inset 0 0 0 2px}.fa-screening button:focus-visible,.fa-screening input:focus-visible,.fa-screening select:focus-visible,.fa-screening textarea:focus-visible,.fa-screening a:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-screening__field{gap:var(--fa-space-1);margin:0 0 var(--fa-space-3);border:0;padding:0;display:grid}.fa-screening__field>span,.fa-screening__field legend{font-weight:600;font-size:var(--fa-font-size-sm);padding:0}.fa-screening__field input,.fa-screening__field select,.fa-screening__field textarea{font:inherit;border:1px solid var(--fa-color-border-strong);border-radius:var(--fa-radius-sm);padding:var(--fa-space-1) var(--fa-space-2);background:var(--fa-color-surface);color:var(--fa-color-text);width:100%}.fa-screening__field textarea{resize:vertical;min-height:84px}.fa-screening__check{gap:var(--fa-space-2);font-size:var(--fa-font-size-sm);align-items:flex-start;margin:2px 0;display:flex}.fa-screening__check>span{overflow-wrap:anywhere;min-width:0}.fa-screening__field input[type=checkbox],.fa-screening__field input[type=radio],.fa-screening__check input{flex:none;width:auto;margin-top:3px}.fa-screening__errors{color:var(--fa-color-danger);font-size:var(--fa-font-size-sm);margin:var(--fa-space-2) 0;padding-left:var(--fa-space-4)}.fa-screening__alert{border-radius:var(--fa-radius-sm);padding:var(--fa-space-2) var(--fa-space-3);margin:0 0 var(--fa-space-3);background:var(--fa-color-danger-soft);color:var(--fa-color-danger)}.fa-screening__alert--warning{background:var(--fa-color-warning-soft);color:var(--fa-color-warning)}.fa-screening__runs{margin:0;padding:0;list-style:none}.fa-screening__runs button{text-align:left;border:0;border-bottom:1px solid var(--fa-color-border);width:100%;padding:var(--fa-space-2) var(--fa-space-1);font:inherit;color:inherit;cursor:pointer;background:0 0;gap:2px;display:grid}.fa-screening__runs button[aria-current=true]{background:var(--fa-color-accent-soft)}.fa-screening__summary{gap:var(--fa-space-2) var(--fa-space-4);font-size:var(--fa-font-size-sm);flex-wrap:wrap;display:flex}.fa-screening__filters{gap:var(--fa-space-2) var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(140px,1fr));display:grid}.fa-screening__filters .fa-screening__field{margin:0}.fa-screening__subject{border-top:2px solid var(--fa-color-border);padding-top:var(--fa-space-2);margin-top:var(--fa-space-2)}.fa-screening__subject:first-of-type{border-top:0;margin-top:0;padding-top:0}.fa-screening__subject-head{justify-content:space-between;gap:var(--fa-space-2);flex-wrap:wrap;align-items:baseline;display:flex}.fa-screening__findings{gap:var(--fa-space-1);margin:var(--fa-space-2) 0;flex-wrap:wrap;display:flex}.fa-screening__findings .fa-badge{white-space:normal;text-align:left}.fa-screening__hits{margin:0;padding:0;list-style:none}.fa-screening__hit{gap:var(--fa-space-1) var(--fa-space-3);text-align:left;width:100%;font:inherit;color:inherit;border-radius:var(--fa-radius-sm);padding:var(--fa-space-2);cursor:pointer;background:0 0;border:1px solid #0000;grid-template-columns:minmax(0,1fr) 120px auto;align-items:center;display:grid}.fa-screening__hit:hover{background:var(--fa-color-surface-sunken)}.fa-screening__hit[aria-current=true]{border-color:var(--fa-color-accent);background:var(--fa-color-accent-soft)}.fa-screening__hit-name{overflow-wrap:anywhere;font-weight:600}.fa-screening__hit-meta{gap:var(--fa-space-1);font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);flex-wrap:wrap;grid-column:1/-1;align-items:center;display:flex}.fa-screening__bar{background:var(--fa-color-surface-sunken);border-radius:4px;height:8px;position:relative}.fa-screening__bar>span{background:var(--fa-color-accent);border-radius:4px;position:absolute;inset:0 auto 0 0}.fa-screening__bar>i{background:var(--fa-color-text);width:2px;position:absolute;top:-3px;bottom:-3px}.fa-screening__score{font-variant-numeric:tabular-nums;text-align:right;font-weight:600}.fa-screening__cmp th,.fa-screening__cmp td{overflow-wrap:break-word;-webkit-hyphens:auto;hyphens:auto}.fa-screening__cmp th[scope=row]{width:28%}.fa-screening__state{text-align:center;width:28px;font-weight:700}.fa-screening__cmp--conflict td{background:var(--fa-color-danger-soft)}.fa-screening__cmp--match .fa-screening__state{color:var(--fa-color-success)}.fa-screening__cmp--conflict .fa-screening__state{color:var(--fa-color-danger)}.fa-screening__cmp--not_compared .fa-screening__state{color:var(--fa-color-text-muted)}.fa-screening__points{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}.fa-screening__steps--plus .fa-screening__points{color:var(--fa-color-success)}.fa-screening__steps--minus .fa-screening__points{color:var(--fa-color-danger)}.fa-screening__steps--result td{border-top:2px solid var(--fa-color-text);font-weight:700}.fa-screening__classes,.fa-screening__actions{gap:var(--fa-space-2);margin:var(--fa-space-2) 0;flex-wrap:wrap;display:flex}.fa-screening__log{font-size:var(--fa-font-size-sm);margin:0;padding:0;list-style:none}.fa-screening__log li{border-left:3px solid var(--fa-color-border);padding:var(--fa-space-1) var(--fa-space-3);margin-bottom:var(--fa-space-2)}.fa-screening__log--decision_recorded{border-color:var(--fa-color-accent)!important}.fa-screening__log--second_review_recorded{border-color:var(--fa-color-success)!important}.fa-screening__source-list{font-size:var(--fa-font-size-sm);margin:0;padding:0;list-style:none}.fa-screening__source-list li{border-bottom:1px solid var(--fa-color-border);padding:var(--fa-space-2) 0;gap:2px;display:grid}.fa-screening__empty{color:var(--fa-color-text-muted);font-style:italic}.fa-screening__sr{clip:rect(0 0 0 0);white-space:nowrap;width:1px;height:1px;position:absolute;overflow:hidden}@media (width<=1100px){.fa-screening__main{grid-template-columns:1fr}}@media (width<=760px){.fa-screening__layout{grid-template-columns:1fr}.fa-screening__hit{grid-template-columns:1fr auto}.fa-screening__hit .fa-screening__bar{display:none}}@media (prefers-reduced-motion:reduce){.fa-screening__btn{transition:none}}.fa-import{gap:var(--fa-space-2);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-import__label,.fa-import__field>span{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-import__file{font:inherit}.fa-import__file:focus-visible,.fa-import select:focus-visible,.fa-import input[type=checkbox]:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-import__grid{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));align-items:end;display:grid}.fa-import__field{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-import select{min-height:2.25rem;padding:0 var(--fa-space-2);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit}.fa-import__check{gap:var(--fa-space-2);align-items:center;display:inline-flex}.fa-import__note{color:var(--fa-color-text-muted);margin:0}.fa-import__warning{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-warning-soft);color:var(--fa-color-warning);margin:0}.fa-sampling{gap:var(--fa-space-4);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-sampling__grid{gap:var(--fa-space-4);grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));align-items:start;display:grid}.fa-sampling__card{gap:var(--fa-space-3);padding:var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-lg);background:var(--fa-color-surface);box-shadow:var(--fa-shadow-sm);flex-direction:column;min-width:0;display:flex}.fa-sampling__card--result{border-color:var(--fa-color-accent);grid-column:1/-1}.fa-sampling__draw-fields{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));align-items:start;display:grid}.fa-sampling__heading{font-size:var(--fa-font-size-md);margin:0;font-weight:600}.fa-sampling__form{gap:var(--fa-space-3);flex-direction:column;display:flex}.fa-sampling__field{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-sampling__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-sampling__input,.fa-sampling__select{box-sizing:border-box;width:100%;min-height:2.25rem;padding:0 var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit}.fa-sampling__input{text-align:end;font-variant-numeric:tabular-nums}.fa-sampling__input--mono{font-family:var(--fa-font-mono);text-align:start}.fa-sampling__input:focus-visible,.fa-sampling__select:focus-visible{border-color:var(--fa-color-accent);box-shadow:var(--fa-focus-ring);outline:none}.fa-sampling__input-wrap{align-items:center;gap:var(--fa-space-2);display:flex}.fa-sampling__unit{min-width:1rem;color:var(--fa-color-text-muted)}.fa-sampling__field--error .fa-sampling__input,.fa-sampling__field--error .fa-sampling__select{border-color:var(--fa-color-danger)}.fa-sampling__error{font-size:var(--fa-font-size-xs);color:var(--fa-color-danger);margin:0}.fa-sampling__hint,.fa-sampling__muted{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs);margin:0}.fa-sampling__actions{gap:var(--fa-space-2);flex-wrap:wrap;display:flex}.fa-sampling__profile p{margin:0 0 var(--fa-space-2)}.fa-sampling__formula{font-family:var(--fa-font-mono);font-size:var(--fa-font-size-xs)}.fa-sampling__id{font-family:var(--fa-font-mono);font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-sampling__note{color:var(--fa-color-text-muted)}.fa-sampling__source code{margin-top:var(--fa-space-1);font-size:var(--fa-font-size-xs);overflow-wrap:anywhere;display:block}.fa-sampling__size{font-variant-numeric:tabular-nums;color:var(--fa-color-accent);margin:0;font-size:1.75rem;font-weight:600}.fa-sampling__warnings{padding:var(--fa-space-2) var(--fa-space-3) var(--fa-space-2) var(--fa-space-5);border-radius:var(--fa-radius);background:var(--fa-color-warning-soft);color:var(--fa-color-warning);margin:0}.fa-sampling__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-sampling__selection{gap:var(--fa-space-3);border-top:1px solid var(--fa-color-border);padding-top:var(--fa-space-3);flex-direction:column;display:flex}.fa-sampling__seed{gap:var(--fa-space-2);flex-wrap:wrap;align-items:center;margin:0;display:flex}.fa-benford{gap:var(--fa-space-4);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-benford__inputs{gap:var(--fa-space-4);grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));align-items:start;display:grid}.fa-benford__card{gap:var(--fa-space-3);padding:var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-lg);background:var(--fa-color-surface);box-shadow:var(--fa-shadow-sm);flex-direction:column;min-width:0;display:flex}.fa-benford__heading{font-size:var(--fa-font-size-md);margin:0;font-weight:600}.fa-benford__field{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-benford__fieldset{gap:var(--fa-space-1);padding:var(--fa-space-2) var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);flex-direction:column;margin:0;display:flex}.fa-benford__radio{gap:var(--fa-space-2);align-items:center;display:inline-flex}.fa-benford__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-benford__select{min-height:2.25rem;padding:0 var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit}.fa-benford__select:focus-visible,.fa-benford__radio input:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-benford__muted,.fa-benford__source{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs);margin:0}.fa-benford__source p{margin:var(--fa-space-1) 0 0;overflow-wrap:anywhere}.fa-benford__error{font-size:var(--fa-font-size-xs);color:var(--fa-color-danger);margin:0}.fa-benford__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-benford__notice{padding:var(--fa-space-2) var(--fa-space-3);border-left:3px solid var(--fa-color-accent);background:var(--fa-color-accent-soft);border-radius:var(--fa-radius-sm);margin:0}.fa-benford__metrics{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));margin:0;display:grid}.fa-benford__metric{gap:var(--fa-space-1);padding:var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-surface-raised);border:1px solid var(--fa-color-border);flex-direction:column;display:flex}.fa-benford__metric dt{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-benford__metric dd{margin:0}.fa-benford__value{font-size:var(--fa-font-size-lg);font-variant-numeric:tabular-nums;font-weight:600}.fa-benford__detail{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-benford__figure{margin:0}.fa-benford__chart{width:100%;height:auto;font:var(--fa-font-size-xs) var(--fa-font-sans);display:block}.fa-benford__grid line{stroke:var(--fa-color-border);stroke-width:1px}.fa-benford__grid text,.fa-benford__axis text{fill:var(--fa-color-text-muted)}.fa-benford__axis line{stroke:var(--fa-color-border-strong)}.fa-benford__bar{fill:var(--fa-color-accent);opacity:.75}.fa-benford__bar--exceeds{fill:var(--fa-color-danger);opacity:.9}.fa-benford__expected{fill:none;stroke:var(--fa-color-text);stroke-width:2px;stroke-dasharray:5 3}.fa-benford__expected-dot{fill:var(--fa-color-surface);stroke:var(--fa-color-text);stroke-width:1.5px}.fa-benford__legend{gap:var(--fa-space-4);margin-top:var(--fa-space-2);font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);flex-wrap:wrap;display:flex}.fa-benford__legend span{align-items:center;gap:var(--fa-space-1);display:inline-flex}.fa-benford__swatch{background:var(--fa-color-accent);opacity:.75;border-radius:2px;width:.9rem;height:.6rem;display:inline-block}.fa-benford__swatch--exceeds{background:var(--fa-color-danger);opacity:.9}.fa-benford__swatch--expected{border-top:2px dashed var(--fa-color-text);opacity:1;background:0 0;height:0}.fa-benford__digits summary{cursor:pointer;margin-bottom:var(--fa-space-2);font-weight:600}.fa-benford__flag{color:var(--fa-color-danger);font-weight:600}@media (prefers-reduced-motion:no-preference){.fa-benford__bar{transition:y var(--fa-transition), height var(--fa-transition)}}.fa-extrapolation{gap:var(--fa-space-4);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-extrapolation__card{gap:var(--fa-space-3);padding:var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-lg);background:var(--fa-color-surface);box-shadow:var(--fa-shadow-sm);flex-direction:column;min-width:0;display:flex}.fa-extrapolation__card--result{border-color:var(--fa-color-accent)}.fa-extrapolation__card--residual{border-style:dashed}.fa-extrapolation__heading{font-size:var(--fa-font-size-md);margin:0;font-weight:600}.fa-extrapolation__settings{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));align-items:start;display:grid}.fa-extrapolation__field{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-extrapolation__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-extrapolation__input,.fa-extrapolation__select{box-sizing:border-box;width:100%;min-height:2.25rem;padding:0 var(--fa-space-2);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit}.fa-extrapolation__input--number{text-align:end;font-variant-numeric:tabular-nums}.fa-extrapolation__input:focus-visible,.fa-extrapolation__select:focus-visible,.fa-extrapolation__check:focus-visible{border-color:var(--fa-color-accent);box-shadow:var(--fa-focus-ring);outline:none}.fa-extrapolation__input[aria-invalid=true],.fa-extrapolation__select[aria-invalid=true]{border-color:var(--fa-color-danger)}.fa-extrapolation__hint,.fa-extrapolation__muted{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs);margin:0}.fa-extrapolation__error{font-size:var(--fa-font-size-xs);color:var(--fa-color-danger);margin:0}.fa-extrapolation__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-extrapolation__scroll{overflow-x:auto}.fa-extrapolation__grid{border-collapse:collapse;width:100%}.fa-extrapolation__grid th{padding:var(--fa-space-1) var(--fa-space-2);text-align:start;font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);white-space:nowrap}.fa-extrapolation__grid td{padding:var(--fa-space-1);vertical-align:top}.fa-extrapolation__grid td .fa-extrapolation__input{min-width:7rem}.fa-extrapolation__grid td .fa-extrapolation__select{min-width:9rem}.fa-extrapolation__actions{gap:var(--fa-space-2);flex-wrap:wrap;align-items:center;display:flex}.fa-extrapolation__source code{margin-top:var(--fa-space-1);font-size:var(--fa-font-size-xs);overflow-wrap:anywhere;display:block}.fa-extrapolation__metrics{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));margin:0;display:grid}.fa-extrapolation__metric{gap:var(--fa-space-1);padding:var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-surface-raised);border:1px solid var(--fa-color-border);flex-direction:column;display:flex}.fa-extrapolation__metric dt{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-extrapolation__metric dd{margin:0}.fa-extrapolation__value{font-size:var(--fa-font-size-md);font-variant-numeric:tabular-nums;font-weight:600}.fa-extrapolation__conclusion{gap:var(--fa-space-2);flex-wrap:wrap;align-items:center;margin:0;display:flex}.fa-extrapolation__list{padding-left:var(--fa-space-5);margin:0}.fa-extrapolation__warnings{padding:var(--fa-space-2) var(--fa-space-3) var(--fa-space-2) var(--fa-space-5);border-radius:var(--fa-radius);background:var(--fa-color-warning-soft);color:var(--fa-color-warning);margin:0}.fa-extrapolation__fingerprint{font-family:var(--fa-font-mono);font-size:var(--fa-font-size-xs);overflow-wrap:anywhere;color:var(--fa-color-text-muted)}.fa-extrapolation__nowrap{white-space:nowrap}.fa-comparisons{gap:var(--fa-space-4);color:var(--fa-color-text);font:var(--fa-font-size-md) / var(--fa-line-height) var(--fa-font-sans);flex-direction:column;display:flex}.fa-comparisons__head{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-comparisons__heading{font-size:var(--fa-font-size-lg);margin:0;line-height:1.3}.fa-comparisons__subheading{font-size:var(--fa-font-size-md);margin:0}.fa-comparisons__note{font-size:var(--fa-font-size-sm);color:var(--fa-color-text-muted);margin:0}.fa-comparisons__state{padding:var(--fa-space-4);border:1px dashed var(--fa-color-border-strong);border-radius:var(--fa-radius);color:var(--fa-color-text-muted);text-align:center;margin:0}.fa-comparisons__state--error{border-style:solid;border-color:var(--fa-color-danger);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);text-align:left}.fa-comparisons__layout{gap:var(--fa-space-5);grid-template-columns:minmax(18rem,2fr) minmax(18rem,3fr);align-items:start;display:grid}.fa-comparisons__layout--single{grid-template-columns:1fr}.fa-comparisons__open{align-items:flex-start;gap:var(--fa-space-3);flex-direction:column;display:flex}.fa-comparisons__open>.fa-synopsis{align-self:stretch}.fa-comparisons__confirm{margin:0}.fa-comparisons button:focus-visible,.fa-comparisons input:focus-visible,.fa-comparisons select:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}@media (width<=52rem){.fa-comparisons__layout{grid-template-columns:1fr}}.fa-comparisons-form{gap:var(--fa-space-3);padding:var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface-raised);flex-direction:column;display:flex}.fa-comparisons-form__options{gap:var(--fa-space-3);flex-direction:column;display:flex}.fa-comparisons-form__row{gap:var(--fa-space-3);flex-wrap:wrap;display:flex}.fa-comparisons-form__row>*{flex:12rem}.fa-comparisons-form__field{gap:var(--fa-space-1);flex-direction:column;min-width:0;display:flex}.fa-comparisons-form__field label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-comparisons-form__field select,.fa-comparisons-form__field input[type=number],.fa-comparisons-form__file input{padding:var(--fa-space-2);border:1px solid var(--fa-color-border-strong);border-radius:var(--fa-radius-sm);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit;font-size:var(--fa-font-size-sm)}.fa-comparisons-form__field--error select,.fa-comparisons-form__field--error input{border-color:var(--fa-color-danger)}.fa-comparisons-form__group{gap:var(--fa-space-2) var(--fa-space-4);padding:var(--fa-space-2) 0 0;border:0;border-top:1px solid var(--fa-color-border);font-size:var(--fa-font-size-sm);flex-wrap:wrap;margin:0;display:flex}.fa-comparisons-form__group legend{padding:0 var(--fa-space-1) 0 0;font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-comparisons-form__group label{align-items:center;gap:var(--fa-space-1);cursor:pointer;display:inline-flex}.fa-comparisons-form__group input{accent-color:var(--fa-color-accent);width:1rem;height:1rem}.fa-comparisons-form__group--kind{border-top:0;padding-top:0}.fa-comparisons-form__hint{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);overflow-wrap:anywhere;margin:0}.fa-comparisons-form__error{font-size:var(--fa-font-size-xs);color:var(--fa-color-danger);flex-basis:100%;margin:0}.fa-comparisons-form__problems{padding:var(--fa-space-2) var(--fa-space-3);border-left:4px solid var(--fa-color-danger);border-radius:var(--fa-radius-sm);background:var(--fa-color-danger-soft);font-size:var(--fa-font-size-sm)}.fa-comparisons-form__problems p{margin:0;font-weight:600}.fa-comparisons-form__problems ul{margin:var(--fa-space-1) 0 0;padding-left:var(--fa-space-5)}.fa-comparisons-form__actions{gap:var(--fa-space-2);flex-wrap:wrap;display:flex}.fa-comparisons-list{gap:var(--fa-space-3);flex-direction:column;display:flex}.fa-comparisons-list__head{justify-content:space-between;align-items:center;gap:var(--fa-space-2);flex-wrap:wrap;display:flex}.fa-comparisons-list__count{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);margin:0}.fa-comparisons-list__items{gap:var(--fa-space-2);flex-direction:column;margin:0;padding:0;list-style:none;display:flex}.fa-comparisons-list__item{gap:var(--fa-space-3);padding:var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);justify-content:space-between;align-items:flex-start;display:flex}.fa-comparisons-list__main{gap:var(--fa-space-1);flex-direction:column;min-width:0;display:flex}.fa-comparisons-list__main p{margin:0}.fa-comparisons-list__title{overflow-wrap:anywhere;font-weight:600}.fa-comparisons-list__meta{align-items:center;gap:var(--fa-space-2);font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);flex-wrap:wrap;display:flex}.fa-comparisons-list__files{font-size:var(--fa-font-size-sm);overflow-wrap:anywhere}.fa-comparisons-list__counts{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-variant-numeric:tabular-nums}.fa-comparisons-list__actions{gap:var(--fa-space-1);flex:none;display:flex}.fa-report{gap:var(--fa-space-4);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-report__card{gap:var(--fa-space-3);padding:var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-lg);background:var(--fa-color-surface);box-shadow:var(--fa-shadow-sm);flex-direction:column;min-width:0;display:flex}.fa-report__heading{font-size:var(--fa-font-size-md);margin:0;font-weight:600}.fa-report__form{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));align-items:end;display:grid}.fa-report__field{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-report__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-report__input{min-height:2.25rem;padding:0 var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit}.fa-report__input:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-report__actions{gap:var(--fa-space-2);flex-wrap:wrap;display:flex}.fa-report__muted,.fa-report__source{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs);margin:0}.fa-report__source p{margin:var(--fa-space-1) 0 0;overflow-wrap:anywhere}.fa-report__error{font-size:var(--fa-font-size-xs);color:var(--fa-color-danger);margin:0}.fa-report__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-report__notice{padding:var(--fa-space-2) var(--fa-space-3);border-left:3px solid var(--fa-color-accent);background:var(--fa-color-accent-soft);border-radius:var(--fa-radius-sm);margin:0}.fa-report__sheet{gap:var(--fa-space-2);flex-direction:column;display:flex}.fa-report__scroll{overflow-x:auto}.fa-report__table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%}.fa-report__table caption{text-align:left;padding-bottom:var(--fa-space-1);font-weight:600}.fa-report__table th,.fa-report__table td{padding:var(--fa-space-1) var(--fa-space-2);border-bottom:1px solid var(--fa-color-border);text-align:left;white-space:nowrap}.fa-report__table th{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-report__table code{font-family:var(--fa-font-mono,monospace)}.fa-ident{gap:var(--fa-space-4);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-ident__head{gap:var(--fa-space-3);flex-wrap:wrap;align-items:flex-end;display:flex}.fa-ident__columns{gap:var(--fa-space-4);grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));align-items:start;display:grid}.fa-ident__card{gap:var(--fa-space-3);padding:var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-lg);background:var(--fa-color-surface);box-shadow:var(--fa-shadow-sm);flex-direction:column;min-width:0;display:flex}.fa-ident__heading{font-size:var(--fa-font-size-md);margin:0;font-weight:600}.fa-ident__form{gap:var(--fa-space-3);flex-direction:column;align-items:flex-start;display:flex}.fa-ident__form>.fa-ident__field{align-self:stretch}.fa-ident__field{gap:var(--fa-space-1);flex-direction:column;min-width:14rem;display:flex}.fa-ident__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-ident__select,.fa-ident__input{min-height:2.25rem;padding:0 var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit}.fa-ident__input{font-family:var(--fa-font-mono)}.fa-ident__input--short{text-transform:uppercase;max-width:6rem}.fa-ident__select:focus-visible,.fa-ident__input:focus-visible,.fa-ident__file:focus-visible,.fa-ident__check input:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-ident__check{gap:var(--fa-space-2);align-items:center;display:inline-flex}.fa-ident__muted,.fa-ident__source{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs);margin:0}.fa-ident__source{flex:20rem}.fa-ident__source p{margin:var(--fa-space-1) 0 0;overflow-wrap:anywhere}.fa-ident__error{font-size:var(--fa-font-size-xs);color:var(--fa-color-danger);margin:0}.fa-ident__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-ident__result,.fa-ident__batch{gap:var(--fa-space-2);padding-top:var(--fa-space-3);border-top:1px solid var(--fa-color-border);flex-direction:column;display:flex}.fa-ident__status{gap:var(--fa-space-2);align-items:center;margin:0;font-weight:600;display:flex}.fa-ident__badge{padding:0 var(--fa-space-2);border-radius:var(--fa-radius-sm);font-size:var(--fa-font-size-xs);white-space:nowrap;background:var(--fa-color-surface-sunken);color:var(--fa-color-text-muted);font-weight:600;display:inline-block}.fa-ident__badge--success{background:var(--fa-color-success-soft);color:var(--fa-color-success)}.fa-ident__badge--danger{background:var(--fa-color-danger-soft);color:var(--fa-color-danger)}.fa-ident__badge--warning{background:var(--fa-color-warning-soft);color:var(--fa-color-warning)}.fa-ident__facts{gap:var(--fa-space-1) var(--fa-space-3);grid-template-columns:max-content 1fr;margin:0;display:grid}.fa-ident__facts dt{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-ident__facts dd{overflow-wrap:anywhere;margin:0}.fa-ident__details summary{cursor:pointer;margin-bottom:var(--fa-space-2);font-weight:600}.fa-ident__summary{margin:0;font-weight:600}.fa-ident__actions{gap:var(--fa-space-3);flex-wrap:wrap;justify-content:space-between;align-items:center;display:flex}.fa-ident__scroll{overflow-x:auto}.fa-ident__table{border-collapse:collapse;width:100%;font-size:var(--fa-font-size-xs)}.fa-ident__table th,.fa-ident__table td{padding:var(--fa-space-1) var(--fa-space-2);border-bottom:1px solid var(--fa-color-border);text-align:left;vertical-align:top}.fa-ident__table th{color:var(--fa-color-text-muted);font-weight:600}.fa-ident__table code{white-space:nowrap}.fa-ident__facts code{overflow-wrap:anywhere}.fa-extraction{gap:var(--fa-space-4);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-extraction__card{gap:var(--fa-space-3);padding:var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-lg);background:var(--fa-color-surface);box-shadow:var(--fa-shadow-sm);flex-direction:column;min-width:0;display:flex}.fa-extraction__heading{font-size:var(--fa-font-size-md);margin:0;font-weight:600}.fa-extraction__form{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));align-items:end;display:grid}.fa-extraction__field{gap:var(--fa-space-1);flex-direction:column;min-width:0;display:flex}.fa-extraction__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-extraction__input{min-height:2.25rem;padding:0 var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit}.fa-extraction__file{font:inherit;color:var(--fa-color-text)}.fa-extraction__input:focus-visible,.fa-extraction__file:focus-visible,.fa-extraction__passed summary:focus-visible,.fa-extraction__pages summary:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-extraction__muted{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs);margin:0}.fa-extraction__error{font-size:var(--fa-font-size-xs);color:var(--fa-color-danger);margin:0}.fa-extraction__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-extraction__notice{padding:var(--fa-space-2) var(--fa-space-3);border-left:3px solid var(--fa-color-accent);background:var(--fa-color-accent-soft);border-radius:var(--fa-radius-sm);margin:0}.fa-extraction__summary{gap:var(--fa-space-1) var(--fa-space-3);grid-template-columns:max-content 1fr;margin:0;display:grid}.fa-extraction__summary dt{color:var(--fa-color-text-muted);font-weight:600}.fa-extraction__summary dd{overflow-wrap:anywhere;margin:0}.fa-extraction__table{border-collapse:collapse;width:100%}.fa-extraction__table th,.fa-extraction__table td{padding:var(--fa-space-2);border-bottom:1px solid var(--fa-color-border);text-align:left;vertical-align:top}.fa-extraction__table th{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-extraction__table td.fa-extraction__number{font-variant-numeric:tabular-nums;white-space:nowrap}.fa-extraction__scroll{overflow-x:auto}.fa-extraction__flags{gap:var(--fa-space-1);flex-wrap:wrap;margin:0;padding:0;list-style:none;display:flex}.fa-extraction__passed summary,.fa-extraction__pages summary{cursor:pointer;font-weight:600}.fa-extraction__text{margin:var(--fa-space-1) 0 0;padding:var(--fa-space-2);white-space:pre-wrap;overflow-wrap:anywhere;background:var(--fa-color-surface-raised);border-radius:var(--fa-radius);font:var(--fa-font-size-xs) / 1.5 var(--fa-font-mono,monospace)}.fa-kanban{--fa-kanban-column-width:17.5rem;gap:var(--fa-space-3);min-width:0;min-height:0;font-family:var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-kanban__banner{align-items:center;gap:var(--fa-space-2);padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-warning-soft);color:var(--fa-color-warning);font-size:var(--fa-font-size-sm);display:flex}.fa-kanban__error{align-items:center;gap:var(--fa-space-2);padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);font-size:var(--fa-font-size-sm);display:flex}.fa-kanban__columns{grid-auto-flow:column;grid-auto-columns:minmax(var(--fa-kanban-column-width), 1fr);gap:var(--fa-space-3);padding-bottom:var(--fa-space-2);align-items:start;display:grid;overflow-x:auto}.fa-kanban__loading{padding:var(--fa-space-6);text-align:center;color:var(--fa-color-text-muted)}.fa-kanban-toolbar{justify-content:space-between;align-items:center;gap:var(--fa-space-3);flex-wrap:wrap;display:flex}.fa-kanban-toolbar__title{align-items:center;gap:var(--fa-space-3);min-width:0;display:flex}.fa-kanban-toolbar__heading{font-size:var(--fa-font-size-lg);letter-spacing:-.01em;margin:0;font-weight:650}.fa-kanban-toolbar__rename{font:inherit;color:inherit;cursor:text;background:0 0;border:0;border-bottom:1px dashed #0000;padding:0}.fa-kanban-toolbar__rename:hover,.fa-kanban-toolbar__rename:focus-visible{border-bottom-color:var(--fa-color-border-strong);outline:none}.fa-kanban-toolbar__title-input{font:650 var(--fa-font-size-lg) var(--fa-font-sans);border:0;border-bottom:2px solid var(--fa-color-accent);color:var(--fa-color-text);background:0 0;outline:none;min-width:12rem}.fa-kanban-toolbar__progress{align-items:center;gap:var(--fa-space-2);font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-variant-numeric:tabular-nums;display:flex}.fa-kanban-toolbar__bar{background:var(--fa-color-surface-sunken);border-radius:999px;width:6rem;height:6px;overflow:hidden}.fa-kanban-toolbar__bar>span{background:var(--fa-color-success);height:100%;transition:width var(--fa-transition);display:block}.fa-kanban-toolbar__tools{align-items:center;gap:var(--fa-space-2);flex-wrap:wrap;display:flex}.fa-kanban-toolbar__search{width:13rem}.fa-kanban-select{min-height:2.25rem;padding:0 var(--fa-space-2);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:var(--fa-font-size-sm) var(--fa-font-sans)}.fa-kanban-select:focus-visible{box-shadow:var(--fa-focus-ring);border-color:var(--fa-color-accent);outline:none}.fa-kanban-column{border-radius:var(--fa-radius-lg);background:var(--fa-color-surface-sunken);border-top:3px solid var(--fa-kanban-column-color,var(--fa-color-border-strong));flex-direction:column;min-height:8rem;max-height:calc(100vh - 12rem);display:flex}.fa-kanban-column--over-limit{box-shadow:inset 0 0 0 2px var(--fa-color-danger)}.fa-kanban-column__head{justify-content:space-between;align-items:center;gap:var(--fa-space-2);padding:var(--fa-space-3) var(--fa-space-3) var(--fa-space-2);display:flex}.fa-kanban-column__name{align-items:center;gap:var(--fa-space-2);font-size:var(--fa-font-size-sm);margin:0;font-weight:650;display:flex}.fa-kanban-column__dot{background:var(--fa-kanban-column-color);border-radius:50%;width:.625rem;height:.625rem}.fa-kanban-column__count{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-variant-numeric:tabular-nums;font-weight:600}.fa-kanban-column__count.is-full{color:var(--fa-color-warning)}.fa-kanban-column__count.is-over{color:var(--fa-color-danger)}.fa-kanban-column__list{gap:var(--fa-space-2);padding:var(--fa-space-1) var(--fa-space-2) var(--fa-space-2);flex-direction:column;flex:1;min-height:3rem;display:flex;overflow-y:auto}.fa-kanban-column__empty{margin:var(--fa-space-2);padding:var(--fa-space-3);border:1px dashed var(--fa-color-border-strong);border-radius:var(--fa-radius);text-align:center;font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-kanban-column__add{margin:0 var(--fa-space-2) var(--fa-space-2);justify-content:flex-start}.fa-kanban-card{--fa-kanban-card-bg:var(--fa-color-surface);--fa-kanban-card-fg:var(--fa-color-text);gap:var(--fa-space-2);padding:var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-kanban-card-bg) center / cover;color:var(--fa-kanban-card-fg);border:1px solid var(--fa-color-border);border-left:3px solid var(--fa-kanban-priority,var(--fa-color-border-strong));box-shadow:var(--fa-shadow-sm);cursor:grab;-webkit-user-select:none;user-select:none;touch-action:manipulation;transition:box-shadow var(--fa-transition), transform var(--fa-transition);flex-direction:column;display:flex;position:relative}.fa-kanban-card:hover{box-shadow:var(--fa-shadow)}.fa-kanban-card:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-kanban-card--hoch{--fa-kanban-priority:var(--fa-color-danger)}.fa-kanban-card--mittel{--fa-kanban-priority:var(--fa-color-warning)}.fa-kanban-card--niedrig{--fa-kanban-priority:var(--fa-color-success)}.fa-kanban-card--styled{border-color:#0000}.fa-kanban-card--grabbed{box-shadow:var(--fa-focus-ring), var(--fa-shadow-lg);transform:rotate(-1deg)}.fa-kanban-card--dragging{opacity:.45;border-style:dashed}.fa-kanban-card--ghost{z-index:1100;pointer-events:none;box-shadow:var(--fa-shadow-lg);opacity:.95;position:fixed;transform:rotate(2deg)}.fa-kanban-card--done .fa-kanban-card__title{opacity:.6;text-decoration:line-through}.fa-kanban-card__head{align-items:flex-start;gap:var(--fa-space-2);display:flex}.fa-kanban-card__title{font-size:var(--fa-font-size-sm);overflow-wrap:anywhere;flex:1;margin:0;font-weight:600;line-height:1.35}.fa-kanban-card__grip{color:var(--fa-color-text-muted);opacity:0;touch-action:none}.fa-kanban-card:hover .fa-kanban-card__grip,.fa-kanban-card:focus-visible .fa-kanban-card__grip{opacity:1}.fa-kanban-card__check{border:2px solid var(--fa-color-border-strong);border-radius:var(--fa-radius-sm);color:#fff;cursor:pointer;background:0 0;flex:none;justify-content:center;align-items:center;width:1.125rem;height:1.125rem;margin-top:1px;padding:0;display:inline-flex}.fa-kanban-card__check[aria-pressed=true]{background:var(--fa-color-success);border-color:var(--fa-color-success)}.fa-kanban-card__check:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-kanban-card__badge{padding:.0625rem var(--fa-space-2);font:700 .6875rem / 1.4 var(--fa-font-mono);letter-spacing:.02em;border-radius:999px;flex:none}.fa-kanban-card__text{font-size:var(--fa-font-size-xs);opacity:.8;margin:0;line-height:1.45}.fa-kanban-card__chips{gap:var(--fa-space-1);flex-wrap:wrap;display:flex}.fa-kanban-card__tag{padding:0 var(--fa-space-2);border-radius:var(--fa-radius-sm);background:color-mix(in srgb, currentColor 10%, transparent);align-items:center;gap:2px;font-size:.6875rem;font-weight:600;line-height:1.6;display:inline-flex}.fa-kanban-card__tag.is-complete{color:var(--fa-color-success)}.fa-kanban-card__meta{align-items:center;gap:var(--fa-space-3);opacity:.85;flex-wrap:wrap;font-size:.6875rem;display:flex}.fa-kanban-card__meta>span{align-items:center;gap:3px;display:inline-flex}.fa-kanban-card__priority{text-transform:uppercase;letter-spacing:.05em;font-weight:700}.fa-kanban-card__priority.is-danger{color:var(--fa-color-danger)}.fa-kanban-card__priority.is-warning{color:var(--fa-color-warning)}.fa-kanban-card__priority.is-success{color:var(--fa-color-success)}.fa-kanban-card--styled .fa-kanban-card__priority{color:inherit}.fa-kanban-card__due.is-overdue{color:var(--fa-color-danger);font-weight:700}.fa-kanban-card__due.is-due_soon{color:var(--fa-color-warning);font-weight:600}.fa-kanban-card__age{margin-left:auto}.fa-kanban-detail{gap:var(--fa-space-4);flex-direction:column;display:flex}.fa-kanban-detail__section{gap:var(--fa-space-2);flex-direction:column;display:flex}.fa-kanban-detail__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);text-transform:uppercase;letter-spacing:.05em;font-weight:650}.fa-kanban-detail__row{gap:var(--fa-space-2);flex-wrap:wrap;align-items:center;display:flex}.fa-kanban-detail__textarea{min-height:6rem;padding:var(--fa-space-2) var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:var(--fa-font-size-sm) / 1.5 var(--fa-font-sans);resize:vertical}.fa-kanban-detail__textarea:focus-visible{border-color:var(--fa-color-accent);box-shadow:var(--fa-focus-ring);outline:none}.fa-kanban-detail__swatch{border-radius:var(--fa-radius-sm);cursor:pointer;border:2px solid #0000;width:1.75rem;height:1.75rem}.fa-kanban-detail__swatch[aria-pressed=true]{border-color:var(--fa-color-text);box-shadow:var(--fa-focus-ring)}.fa-kanban-detail__swatch:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-kanban-detail__list{gap:var(--fa-space-1);flex-direction:column;margin:0;padding:0;list-style:none;display:flex}.fa-kanban-detail__item{align-items:center;gap:var(--fa-space-2);padding:var(--fa-space-1) var(--fa-space-2);border-radius:var(--fa-radius-sm);background:var(--fa-color-surface-raised);display:flex}.fa-kanban-detail__item input[type=text]{color:inherit;font:inherit;background:0 0;border:0;flex:1}.fa-kanban-detail__item.is-done input[type=text]{color:var(--fa-color-text-muted);text-decoration:line-through}.fa-kanban-detail__meta{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);border-top:1px solid var(--fa-color-border);padding-top:var(--fa-space-3)}.fa-kanban-detail__image{object-fit:cover;border-radius:var(--fa-radius);width:100%;height:5rem}.fa-kanban-settings__row{gap:var(--fa-space-2);padding:var(--fa-space-2);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface-raised);grid-template-columns:auto 1fr 5.5rem auto auto;align-items:end;display:grid}.fa-kanban-settings__colors{gap:var(--fa-space-1);flex-wrap:wrap;grid-column:1/-1;align-items:center;display:flex}.fa-kanban-settings__list{gap:var(--fa-space-2);flex-direction:column;margin:0;padding:0;list-style:none;display:flex}.fa-kanban-settings__check{align-items:center;gap:var(--fa-space-1);font-size:var(--fa-font-size-xs);display:inline-flex}.fa-kanban-settings__hint{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-kanban-share__results{border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);max-height:12rem;margin:0;padding:0;list-style:none;overflow-y:auto}.fa-kanban-share__results button{text-align:start;width:100%;padding:var(--fa-space-2) var(--fa-space-3);color:inherit;font:inherit;cursor:pointer;background:0 0;border:0}.fa-kanban-share__results button:hover,.fa-kanban-share__results button:focus-visible{background:var(--fa-color-accent-soft);outline:none}.fa-kanban-share__person{align-items:center;gap:var(--fa-space-3);padding:var(--fa-space-2) 0;border-bottom:1px solid var(--fa-color-border);display:flex}.fa-kanban-share__avatar{background:var(--fa-color-accent-soft);width:2rem;height:2rem;color:var(--fa-color-accent);font-size:var(--fa-font-size-xs);border-radius:50%;justify-content:center;align-items:center;font-weight:700;display:inline-flex}.fa-kanban-share__name{font-size:var(--fa-font-size-sm);flex:1}.fa-kanban-boards{gap:var(--fa-space-3);font-family:var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-kanban-boards__group{font-size:var(--fa-font-size-xs);text-transform:uppercase;letter-spacing:.06em;color:var(--fa-color-text-muted);margin:0}.fa-kanban-boards__list{gap:var(--fa-space-1);flex-direction:column;margin:0;padding:0;list-style:none;display:flex}.fa-kanban-boards__item{gap:var(--fa-space-2);padding:var(--fa-space-2);border-radius:var(--fa-radius);grid-template-columns:auto 1fr auto;align-items:center;display:grid}.fa-kanban-boards__item.is-active{background:var(--fa-color-accent-soft)}.fa-kanban-boards__open{min-width:0;color:inherit;font:inherit;text-align:start;cursor:pointer;background:0 0;border:0;flex-direction:column;gap:2px;padding:0;display:flex}.fa-kanban-boards__open:focus-visible{box-shadow:var(--fa-focus-ring);border-radius:var(--fa-radius-sm);outline:none}.fa-kanban-boards__name{font-size:var(--fa-font-size-sm);text-overflow:ellipsis;white-space:nowrap;font-weight:600;overflow:hidden}.fa-kanban-boards__sub{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-kanban-boards__templates{gap:var(--fa-space-2);grid-template-columns:repeat(auto-fill,minmax(9rem,1fr));display:grid}.fa-kanban-boards__template{padding:var(--fa-space-2);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:inherit;font:inherit;text-align:start;cursor:pointer;flex-direction:column;gap:2px;display:flex}.fa-kanban-boards__template[aria-pressed=true]{border-color:var(--fa-color-accent);box-shadow:var(--fa-focus-ring)}@media (prefers-reduced-motion:reduce){.fa-kanban-card,.fa-kanban-card--grabbed,.fa-kanban-card--ghost{transition:none;transform:none}}.fa-kanban-detail__chip-remove{color:inherit;cursor:pointer;opacity:.7;background:0 0;border:0;margin-left:2px;padding:0;display:inline-flex}.fa-kanban-detail__chip-remove:hover,.fa-kanban-detail__chip-remove:focus-visible{opacity:1;outline:none}.fa-kanban-detail__meta-inline{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);margin-left:auto}.fa-db-kanban{--fa-db-kanban-column-width:16rem;gap:var(--fa-space-3);color:var(--fa-color-text);font:var(--fa-font-size-md) / var(--fa-line-height) var(--fa-font-sans);flex-direction:column;display:flex}.fa-db-kanban__toolbar{align-items:flex-end;gap:var(--fa-space-3) var(--fa-space-4);flex-wrap:wrap;display:flex}.fa-db-kanban__title{font-size:var(--fa-font-size-lg);align-self:center;margin:0 auto 0 0;line-height:1.3}.fa-db-kanban__group{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-db-kanban__group label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-db-kanban__group select{padding:var(--fa-space-2);border:1px solid var(--fa-color-border-strong);border-radius:var(--fa-radius-sm);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit;font-size:var(--fa-font-size-sm)}.fa-db-kanban__search{min-width:14rem}.fa-db-kanban__readonly{padding:var(--fa-space-1) var(--fa-space-2);border-radius:var(--fa-radius-sm);background:var(--fa-color-warning-soft);font-size:var(--fa-font-size-xs);font-weight:600}.fa-db-kanban__state{padding:var(--fa-space-4);border:1px dashed var(--fa-color-border-strong);border-radius:var(--fa-radius);color:var(--fa-color-text-muted);text-align:center;margin:0}.fa-db-kanban__state--error{border-style:solid;border-color:var(--fa-color-danger);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);text-align:left}.fa-db-kanban__columns{grid-auto-flow:column;grid-auto-columns:minmax(var(--fa-db-kanban-column-width), 1fr);gap:var(--fa-space-3);padding-bottom:var(--fa-space-2);align-items:start;display:grid;overflow-x:auto}.fa-db-kanban select:focus-visible,.fa-db-kanban button:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-db-kanban-column{gap:var(--fa-space-2);min-height:8rem;padding:var(--fa-space-2);border-radius:var(--fa-radius-lg);border-top:3px solid var(--fa-color-accent);background:var(--fa-color-surface-sunken);transition:box-shadow var(--fa-transition);flex-direction:column;display:flex}.fa-db-kanban-column--empty-value{border-top-color:var(--fa-color-border-strong)}.fa-db-kanban-column--over{box-shadow:inset 0 0 0 2px var(--fa-color-accent)}.fa-db-kanban-column__head{justify-content:space-between;align-items:baseline;gap:var(--fa-space-2);padding:var(--fa-space-1) var(--fa-space-1) 0;display:flex}.fa-db-kanban-column__name{font-size:var(--fa-font-size-sm);overflow-wrap:anywhere;margin:0;font-weight:650}.fa-db-kanban-column__count{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-variant-numeric:tabular-nums;flex:none;font-weight:600}.fa-db-kanban-column__list{gap:var(--fa-space-2);flex-direction:column;margin:0;padding:0;list-style:none;display:flex}.fa-db-kanban-column__empty{padding:var(--fa-space-2);font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);text-align:center;margin:0}.fa-db-kanban-column__add{align-self:flex-start}.fa-db-kanban-card{padding:var(--fa-space-2) var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);box-shadow:var(--fa-shadow-sm);cursor:grab}.fa-db-kanban-card[draggable=false]{cursor:default}.fa-db-kanban-card:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-db-kanban-card--dragging{opacity:.5}.fa-db-kanban-card__title{font-size:var(--fa-font-size-sm);overflow-wrap:anywhere;margin:0;font-weight:600}.fa-db-kanban-card__fields{margin:var(--fa-space-1) 0 0;flex-direction:column;gap:.125rem;display:flex}.fa-db-kanban-card__field{column-gap:var(--fa-space-2);font-size:var(--fa-font-size-xs);flex-wrap:wrap;display:flex}.fa-db-kanban-card__field dt{color:var(--fa-color-text-muted)}.fa-db-kanban-card__field dt:after{content:\":\"}.fa-db-kanban-card__field dd{overflow-wrap:break-word;font-variant-numeric:tabular-nums;min-width:0;margin:0}@media (prefers-reduced-motion:reduce){.fa-db-kanban-column{transition:none}}.fa-batchchecks{gap:var(--fa-space-4);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-batchchecks__card{gap:var(--fa-space-3);padding:var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-lg);background:var(--fa-color-surface);box-shadow:var(--fa-shadow-sm);flex-direction:column;min-width:0;display:flex}.fa-batchchecks__heading{font-size:var(--fa-font-size-md);margin:0;font-weight:600}.fa-batchchecks__subheading{font-size:var(--fa-font-size-sm);margin:0;font-weight:600}.fa-batchchecks__grid{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));align-items:end;display:grid}.fa-batchchecks__field{gap:var(--fa-space-1);flex-direction:column;min-width:0;display:flex}.fa-batchchecks__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-batchchecks__input{min-height:2.25rem;padding:0 var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit}.fa-batchchecks__file{font:inherit;color:var(--fa-color-text)}.fa-batchchecks__check{gap:var(--fa-space-2);align-items:center;display:flex}.fa-batchchecks__input:focus-visible,.fa-batchchecks__file:focus-visible,.fa-batchchecks__check input:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-batchchecks__muted{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs);margin:0}.fa-batchchecks__error{font-size:var(--fa-font-size-xs);color:var(--fa-color-danger);margin:0}.fa-batchchecks__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-batchchecks__notice{padding:var(--fa-space-2) var(--fa-space-3);border-left:3px solid var(--fa-color-accent);background:var(--fa-color-accent-soft);border-radius:var(--fa-radius-sm);margin:0}.fa-batchchecks__summary{gap:var(--fa-space-1) var(--fa-space-3);grid-template-columns:max-content 1fr;margin:0;display:grid}.fa-batchchecks__summary dt{color:var(--fa-color-text-muted);font-weight:600}.fa-batchchecks__summary dd{overflow-wrap:anywhere;font-variant-numeric:tabular-nums;margin:0}.fa-batchchecks__actions{gap:var(--fa-space-2);flex-wrap:wrap;display:flex}.fa-batchchecks__scroll{overflow-x:auto}.fa-batchchecks__table{border-collapse:collapse;width:100%}.fa-batchchecks__table th,.fa-batchchecks__table td{padding:var(--fa-space-2);border-bottom:1px solid var(--fa-color-border);text-align:left;vertical-align:top}.fa-batchchecks__table thead th{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-batchchecks__table tbody th{white-space:nowrap;font-weight:600}.fa-batchchecks__note{margin-top:var(--fa-space-1);color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs);display:block}.fa-samplesize{gap:var(--fa-space-3);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-samplesize__form,.fa-samplesize__result{gap:var(--fa-space-3);flex-direction:column;display:flex}.fa-samplesize__fields{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fill,minmax(16rem,1fr));display:grid}.fa-samplesize__field{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-samplesize__label{font-weight:600}.fa-samplesize__input,.fa-samplesize__select{padding:var(--fa-space-1) var(--fa-space-2);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:inherit;font:inherit}.fa-samplesize__input:focus-visible,.fa-samplesize__select:focus-visible,.fa-samplesize__submit:focus-visible,.fa-samplesize__add:focus-visible,.fa-samplesize__remove:focus-visible{border-color:var(--fa-color-accent);box-shadow:var(--fa-focus-ring);outline:none}.fa-samplesize__input[aria-invalid=true],.fa-samplesize__select[aria-invalid=true]{border-color:var(--fa-color-danger)}.fa-samplesize__error{color:var(--fa-color-danger)}.fa-samplesize__check{gap:var(--fa-space-2);align-items:center;display:flex}.fa-samplesize__strata{padding:var(--fa-space-2);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);margin:0}.fa-samplesize__table{border-collapse:collapse;width:100%}.fa-samplesize__table caption{text-align:start;padding-block:var(--fa-space-1);font-weight:600}.fa-samplesize__table th,.fa-samplesize__table td{padding:var(--fa-space-1) var(--fa-space-2);border-bottom:1px solid var(--fa-color-border);text-align:start;vertical-align:top}.fa-samplesize__submit,.fa-samplesize__add,.fa-samplesize__remove{padding:var(--fa-space-2) var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:inherit;font:inherit;cursor:pointer;align-self:flex-start}.fa-samplesize__submit{border-color:var(--fa-color-accent)}.fa-samplesize__submit:disabled{cursor:not-allowed;opacity:.6}.fa-samplesize__source code{font-family:var(--fa-font-mono,monospace)}.fa-samplesize__heading{font-size:var(--fa-font-size-md,1rem);margin:0}.fa-samplesize__badge{padding:0 var(--fa-space-2);border:1px solid var(--fa-color-accent);border-radius:var(--fa-radius);font-size:var(--fa-font-size-sm);margin-inline-start:var(--fa-space-2);font-weight:400}.fa-samplesize__summary{gap:var(--fa-space-4);flex-wrap:wrap;margin:0;display:flex}.fa-samplesize__summary dt{color:var(--fa-color-text-muted)}.fa-samplesize__summary dd{font-size:var(--fa-font-size-lg,1.25rem);margin:0;font-weight:600}.fa-samplesize__warnings{color:var(--fa-color-text-muted);margin:0;padding-inline-start:var(--fa-space-4)}.fa-samplesize__muted{color:var(--fa-color-text-muted);margin:0}.fa-samplesize__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-attributes{gap:var(--fa-space-3);padding:var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-lg);background:var(--fa-color-surface);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-attributes__heading{font-size:var(--fa-font-size-md);margin:0;font-weight:600}.fa-attributes__form{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));align-items:start;display:grid}.fa-attributes__field{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-attributes__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-attributes__input,.fa-attributes__select{box-sizing:border-box;width:100%;min-height:2.25rem;padding:0 var(--fa-space-2);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit}.fa-attributes__input{text-align:end;font-variant-numeric:tabular-nums}.fa-attributes__input:focus-visible,.fa-attributes__select:focus-visible{border-color:var(--fa-color-accent);box-shadow:var(--fa-focus-ring);outline:none}.fa-attributes__input[aria-invalid=true]{border-color:var(--fa-color-danger)}.fa-attributes__error{color:var(--fa-color-danger);font-size:var(--fa-font-size-xs)}.fa-attributes__actions{gap:var(--fa-space-2);flex-wrap:wrap;align-items:center;display:flex}.fa-attributes__metrics{gap:var(--fa-space-2);grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));margin:0;display:grid}.fa-attributes__metric{gap:var(--fa-space-1);padding:var(--fa-space-2);border-radius:var(--fa-radius);background:var(--fa-color-surface-sunken);flex-direction:column;display:flex}.fa-attributes__metric dt{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-attributes__metric dd{font-variant-numeric:tabular-nums;margin:0;font-weight:600}.fa-attributes__muted{color:var(--fa-color-text-muted);margin:0}.fa-attributes__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-reporttemplates{gap:var(--fa-space-4);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-reporttemplates__card{gap:var(--fa-space-3);padding:var(--fa-space-4);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius-lg);background:var(--fa-color-surface);box-shadow:var(--fa-shadow-sm);flex-direction:column;min-width:0;display:flex}.fa-reporttemplates__heading{font-size:var(--fa-font-size-md);margin:0;font-weight:600}.fa-reporttemplates__form{gap:var(--fa-space-3);grid-template-columns:repeat(auto-fit,minmax(12rem,1fr));align-items:end;display:grid}.fa-reporttemplates__field{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-reporttemplates__label{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted);font-weight:600}.fa-reporttemplates__input{min-height:2.25rem;padding:0 var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);color:var(--fa-color-text);font:inherit}.fa-reporttemplates__input:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-reporttemplates__actions{gap:var(--fa-space-2);flex-wrap:wrap;display:flex}.fa-reporttemplates__muted{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs);margin:0}.fa-reporttemplates__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-reporttemplates__notice{padding:var(--fa-space-2) var(--fa-space-3);border-left:3px solid var(--fa-color-accent);background:var(--fa-color-accent-soft);border-radius:var(--fa-radius-sm);margin:0}.fa-reporttemplates__scroll{overflow-x:auto}.fa-reporttemplates__table{border-collapse:collapse;width:100%}.fa-reporttemplates__table th,.fa-reporttemplates__table td{padding:var(--fa-space-1) var(--fa-space-2);border-bottom:1px solid var(--fa-color-border);text-align:left;vertical-align:top}.fa-reporttemplates__table th{font-size:var(--fa-font-size-xs);color:var(--fa-color-text-muted)}.fa-reporttemplates__table code,.fa-reporttemplates__issues code{font-family:var(--fa-font-mono,monospace)}.fa-reporttemplates__blocks,.fa-reporttemplates__issues{padding-left:var(--fa-space-4);gap:var(--fa-space-1);flex-direction:column;margin:0;display:flex}.fa-reporttemplates__issues{color:var(--fa-color-danger)}.fa-reporttemplates__frame{border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:#fff;width:100%;min-height:24rem}.fa-runner{gap:var(--fa-space-3);font:var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans);color:var(--fa-color-text);flex-direction:column;display:flex}.fa-runner__kopf{justify-content:space-between;align-items:baseline;gap:var(--fa-space-2);flex-wrap:wrap;display:flex}.fa-runner__titel{font-size:var(--fa-font-size-lg);margin:0}.fa-runner__meta{color:var(--fa-color-text-muted);margin:0}.fa-runner__reiter{gap:var(--fa-space-1);border-bottom:1px solid var(--fa-color-border);flex-wrap:wrap;display:flex}.fa-runner__tab{padding:var(--fa-space-2) var(--fa-space-3);color:var(--fa-color-text-muted);font:inherit;cursor:pointer;background:0 0;border:0;border-bottom:2px solid #0000}.fa-runner__tab[aria-selected=true]{border-bottom-color:var(--fa-color-accent);color:var(--fa-color-text);font-weight:600}.fa-runner__tab:focus-visible,.fa-runner__panel:focus-visible{box-shadow:var(--fa-focus-ring);border-radius:var(--fa-radius-sm);outline:none}.fa-runner__panel{gap:var(--fa-space-3);flex-direction:column;display:flex}.fa-runner__zwischen{align-items:center;gap:var(--fa-space-2);font-size:var(--fa-font-size-md);margin:0;display:flex}.fa-runner__muted{color:var(--fa-color-text-muted);margin:0}.fa-runner__failure{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-runner__meldung{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);margin:0}.fa-runner__meldung--success{background:var(--fa-color-success-soft);color:var(--fa-color-success)}.fa-runner__meldung--warning{background:var(--fa-color-warning-soft);color:var(--fa-color-warning)}.fa-runner__hinweise{gap:var(--fa-space-1);flex-direction:column;margin:0;padding:0;list-style:none;display:flex}.fa-runner__hinweis{padding:var(--fa-space-2) var(--fa-space-3);border-radius:var(--fa-radius);border-left:3px solid var(--fa-color-border-strong);background:var(--fa-color-surface-sunken)}.fa-runner__hinweis--danger{border-left-color:var(--fa-color-danger);background:var(--fa-color-danger-soft)}.fa-runner__hinweis--warning{border-left-color:var(--fa-color-warning);background:var(--fa-color-warning-soft)}.fa-runner__hinweis--info{border-left-color:var(--fa-color-accent);background:var(--fa-color-accent-soft)}.fa-runner__daten{gap:var(--fa-space-2);grid-template-columns:repeat(auto-fill,minmax(14rem,1fr));margin:0;display:grid}.fa-runner__datum{padding:var(--fa-space-2) var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface)}.fa-runner__datum dt{color:var(--fa-color-text-muted);font-size:var(--fa-font-size-xs)}.fa-runner__datum dd{overflow-wrap:anywhere;margin:0}.fa-runner__tabelle{border-collapse:collapse;width:100%}.fa-runner__tabelle caption{padding-bottom:var(--fa-space-1);text-align:start;font-weight:600}.fa-runner__tabelle th,.fa-runner__tabelle td{padding:var(--fa-space-1) var(--fa-space-2);border-bottom:1px solid var(--fa-color-border);text-align:start;vertical-align:top}.fa-runner__tabelle thead th{color:var(--fa-color-text-muted);font-weight:600}.fa-runner__formular{gap:var(--fa-space-3);flex-direction:column;display:flex}.fa-runner__abschnitt{gap:var(--fa-space-2) var(--fa-space-4);padding:var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);grid-template-columns:repeat(auto-fill,minmax(16rem,1fr));margin:0;display:grid}.fa-runner__abschnitt legend{padding:0 var(--fa-space-1);font-weight:600}.fa-runner__feld{gap:var(--fa-space-1);flex-direction:column;display:flex}.fa-runner__feld--schalter{flex-direction:row;align-items:center}.fa-runner__eingabe{padding:var(--fa-space-1) var(--fa-space-2);border:1px solid var(--fa-color-border-strong);border-radius:var(--fa-radius-sm);background:var(--fa-color-surface);color:inherit;font:inherit}.fa-runner__eingabe:focus-visible,.fa-runner__feld input[type=checkbox]:focus-visible{box-shadow:var(--fa-focus-ring);outline:none}.fa-runner__eingabe[aria-invalid=true]{border-color:var(--fa-color-danger)}.fa-runner__eingabe:disabled{opacity:.7}.fa-runner__feldfehler{color:var(--fa-color-danger);font-size:var(--fa-font-size-xs);margin:0}.fa-runner__probleme{padding:var(--fa-space-2) var(--fa-space-3) var(--fa-space-2) var(--fa-space-6);border-radius:var(--fa-radius);background:var(--fa-color-danger-soft);color:var(--fa-color-danger);margin:0}.fa-runner__aktionen{align-items:center;gap:var(--fa-space-2);flex-wrap:wrap;display:flex}.fa-runner__vorschau,.fa-runner__konflikt{gap:var(--fa-space-2);padding:var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface-raised);flex-direction:column;display:flex}.fa-runner__konflikt{border-color:var(--fa-color-warning)}.fa-runner__diff summary{cursor:pointer;font-family:var(--fa-font-mono)}.fa-runner__diff pre,.fa-runner__befehl{padding:var(--fa-space-2);border-radius:var(--fa-radius-sm);background:var(--fa-color-surface-sunken);font:var(--fa-font-size-xs) / var(--fa-line-height) var(--fa-font-mono);margin:0;overflow-x:auto}.fa-runner__befehl{-webkit-user-select:all;user-select:all}.fa-runner__schritte{padding-left:var(--fa-space-5);font-family:var(--fa-font-mono);font-size:var(--fa-font-size-xs);margin:0}.fa-runner__prioritaeten{gap:var(--fa-space-1);flex-direction:column;margin:0;padding:0;list-style:none;display:flex}.fa-runner__prioritaet{align-items:center;gap:var(--fa-space-2) var(--fa-space-3);padding:var(--fa-space-2) var(--fa-space-3);border:1px solid var(--fa-color-border);border-radius:var(--fa-radius);background:var(--fa-color-surface);flex-wrap:wrap;display:flex}.fa-runner__rang{min-width:4.5rem;color:var(--fa-color-text-muted)}.fa-runner__klasse{flex:8rem}.fa-runner__schmal{width:6rem}.fa-runner__klassenname{grid-column:1/-1}.fa-runner__klassenname .fa-runner__eingabe{flex:12rem}";
//#endregion
//#region ../../node_modules/@vue/shared/dist/shared.esm-bundler.js
// @__NO_SIDE_EFFECTS__
function t(e) {
	let t = /* @__PURE__ */ Object.create(null);
	for (let n of e.split(",")) t[n] = 1;
	return (e) => e in t;
}
var n = {}, r = [], i = () => {}, a = () => !1, o = (e) => e.charCodeAt(0) === 111 && e.charCodeAt(1) === 110 && (e.charCodeAt(2) > 122 || e.charCodeAt(2) < 97), s = (e) => e.startsWith("onUpdate:"), c = Object.assign, l = (e, t) => {
	let n = e.indexOf(t);
	n > -1 && e.splice(n, 1);
}, u = Object.prototype.hasOwnProperty, d = (e, t) => u.call(e, t), f = Array.isArray, p = (e) => S(e) === "[object Map]", m = (e) => S(e) === "[object Set]", h = (e) => S(e) === "[object Date]", g = (e) => typeof e == "function", _ = (e) => typeof e == "string", v = (e) => typeof e == "symbol", y = (e) => typeof e == "object" && !!e, b = (e) => (y(e) || g(e)) && g(e.then) && g(e.catch), x = Object.prototype.toString, S = (e) => x.call(e), C = (e) => S(e).slice(8, -1), w = (e) => S(e) === "[object Object]", ee = (e) => _(e) && e !== "NaN" && e[0] !== "-" && "" + parseInt(e, 10) === e, te = /* @__PURE__ */ t(",key,ref,ref_for,ref_key,onVnodeBeforeMount,onVnodeMounted,onVnodeBeforeUpdate,onVnodeUpdated,onVnodeBeforeUnmount,onVnodeUnmounted"), ne = (e) => {
	let t = /* @__PURE__ */ Object.create(null);
	return ((n) => t[n] || (t[n] = e(n)));
}, re = /-\w/g, T = ne((e) => e.replace(re, (e) => e.slice(1).toUpperCase())), ie = /\B([A-Z])/g, E = ne((e) => e.replace(ie, "-$1").toLowerCase()), ae = ne((e) => e.charAt(0).toUpperCase() + e.slice(1)), oe = ne((e) => e ? `on${ae(e)}` : ""), se = (e, t) => !Object.is(e, t), D = (e, ...t) => {
	for (let n = 0; n < e.length; n++) e[n](...t);
}, ce = (e, t, n, r = !1) => {
	Object.defineProperty(e, t, {
		configurable: !0,
		enumerable: !1,
		writable: r,
		value: n
	});
}, le = (e) => {
	let t = parseFloat(e);
	return isNaN(t) ? e : t;
}, ue = (e) => {
	let t = _(e) ? Number(e) : NaN;
	return isNaN(t) ? e : t;
}, de, fe = () => de ||= typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
function pe(e) {
	if (f(e)) {
		let t = {};
		for (let n = 0; n < e.length; n++) {
			let r = e[n], i = _(r) ? _e(r) : pe(r);
			if (i) for (let e in i) t[e] = i[e];
		}
		return t;
	}
	if (_(e) || y(e)) return e;
}
var me = /;(?![^(]*\))/g, he = /:([^]+)/, ge = /"(?:[^"\\]|\\[^])*"|'(?:[^'\\]|\\[^])*'|\\[^]|\/\*[^]*?\*\//g;
function _e(e) {
	let t = {};
	return e.replace(ge, (e) => e.startsWith("/*") ? "" : e).split(me).forEach((e) => {
		if (e) {
			let n = e.split(he);
			n.length > 1 && (t[n[0].trim()] = n[1].trim());
		}
	}), t;
}
function ve(e) {
	let t = "";
	if (_(e)) t = e;
	else if (f(e)) for (let n = 0; n < e.length; n++) {
		let r = ve(e[n]);
		r && (t += r + " ");
	}
	else if (y(e)) for (let n in e) e[n] && (t += n + " ");
	return t.trim();
}
var ye = "itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly", be = /* @__PURE__ */ t(ye);
ye + "";
function xe(e) {
	return !!e || e === "";
}
function Se(e, t, n) {
	if (e.length !== t.length) return !1;
	let r = !0;
	for (let i = 0; r && i < e.length; i++) r = Ee(e[i], t[i], n);
	return r;
}
function Ce(e, t, n) {
	if (e.size !== t.size) return !1;
	let r = Array.from(t), i = new Uint8Array(r.length);
	for (let t of e) {
		let e = -1;
		for (let a = 0; a < r.length; a++) if (!i[a] && Ee(t, r[a], n)) {
			e = a;
			break;
		}
		if (e < 0) return !1;
		i[e] = 1;
	}
	return !0;
}
function we(e, t, n) {
	let r = p(e), i = p(t);
	if (r || i || (r = m(e), i = m(t), r || i)) return r && i ? Ce(e, t, n) : !1;
	if (Object.keys(e).length !== Object.keys(t).length) return !1;
	for (let r in e) {
		let i = e.hasOwnProperty(r), a = t.hasOwnProperty(r);
		if (i && !a || !i && a || !Ee(e[r], t[r], n)) return !1;
	}
	return String(e) === String(t);
}
function Te(e, t, n, r) {
	n ||= [/* @__PURE__ */ new Map(), /* @__PURE__ */ new Map()];
	let [i, a] = n;
	if (i.has(e) || a.has(t)) return i.get(e) === t && a.get(t) === e;
	i.set(e, t), a.set(t, e);
	let o = r(e, t, n);
	return i.delete(e), a.delete(t), o;
}
function Ee(e, t, n) {
	if (e === t) return !0;
	let r = h(e), i = h(t);
	return r || i ? r && i ? e.getTime() === t.getTime() : !1 : (r = v(e), i = v(t), r || i ? e === t : (r = f(e), i = f(t), r || i ? r && i ? Te(e, t, n, Se) : !1 : (r = y(e), i = y(t), r || i ? !r || !i ? !1 : Te(e, t, n, we) : String(e) === String(t))));
}
var De = (e) => !!(e && e.__v_isRef === !0), O = (e) => _(e) ? e : e == null ? "" : f(e) || y(e) && (e.toString === x || !g(e.toString)) ? De(e) ? O(e.value) : JSON.stringify(e, Oe, 2) : String(e), Oe = (e, t) => De(t) ? Oe(e, t.value) : p(t) ? { [`Map(${t.size})`]: [...t.entries()].reduce((e, [t, n], r) => (e[ke(t, r) + " =>"] = n, e), {}) } : m(t) ? { [`Set(${t.size})`]: [...t.values()].map((e) => ke(e)) } : v(t) ? ke(t) : y(t) && !f(t) && !w(t) ? String(t) : t, ke = (e, t = "") => v(e) ? `Symbol(${e.description ?? t})` : e, k, Ae = class {
	constructor(e = !1) {
		this.detached = e, this._active = !0, this._on = 0, this.effects = [], this.cleanups = [], this._isPaused = !1, this._warnOnRun = !0, this.__v_skip = !0, !e && k && (k.active ? (this.parent = k, this.index = (k.scopes || (k.scopes = [])).push(this) - 1) : (this._active = !1, this._warnOnRun = !1));
	}
	get active() {
		return this._active;
	}
	pause() {
		if (this._active) {
			this._isPaused = !0;
			let e, t;
			if (this.scopes) {
				let n = this.scopes.slice();
				for (e = 0, t = n.length; e < t; e++) n[e].pause();
			}
			for (e = 0, t = this.effects.length; e < t; e++) this.effects[e].pause();
		}
	}
	resume() {
		if (this._active && this._isPaused) {
			this._isPaused = !1;
			let e, t;
			if (this.scopes) {
				let n = this.scopes.slice();
				for (e = 0, t = n.length; e < t; e++) n[e].resume();
			}
			let n = this.effects.slice();
			for (e = 0, t = n.length; e < t; e++) n[e].resume();
		}
	}
	run(e) {
		if (this._active) {
			let t = k;
			try {
				return k = this, e();
			} finally {
				k = t;
			}
		}
	}
	on() {
		++this._on === 1 && (this.prevScope = k, k = this);
	}
	off() {
		if (this._on > 0 && --this._on === 0) {
			if (k === this) k = this.prevScope;
			else {
				let e = k;
				for (; e;) {
					if (e.prevScope === this) {
						e.prevScope = this.prevScope;
						break;
					}
					e = e.prevScope;
				}
			}
			this.prevScope = void 0;
		}
	}
	stop(e) {
		if (this._active) {
			this._active = !1;
			let t, n;
			for (t = 0, n = this.effects.length; t < n; t++) this.effects[t].stop();
			for (this.effects.length = 0, t = 0, n = this.cleanups.length; t < n; t++) this.cleanups[t]();
			if (this.cleanups.length = 0, this.scopes) {
				let e = this.scopes.slice();
				for (t = 0, n = e.length; t < n; t++) e[t].stop(!0);
				this.scopes.length = 0;
			}
			if (!this.detached && this.parent && !e) {
				let e = this.parent.scopes.pop();
				e && e !== this && (this.parent.scopes[this.index] = e, e.index = this.index);
			}
			this.parent = void 0;
		}
	}
};
function je() {
	return k;
}
function Me(e, t = !1) {
	k && k.cleanups.push(e);
}
var A, Ne = /* @__PURE__ */ new WeakSet(), Pe = class {
	constructor(e) {
		this.fn = e, this.deps = void 0, this.depsTail = void 0, this.flags = 5, this.next = void 0, this.cleanup = void 0, this.scheduler = void 0, k && (k.active ? k.effects.push(this) : this.flags &= -2);
	}
	pause() {
		this.flags |= 64;
	}
	resume() {
		this.flags & 64 && (this.flags &= -65, Ne.has(this) && (Ne.delete(this), this.trigger()));
	}
	notify() {
		this.flags & 2 && !(this.flags & 32) || this.flags & 8 || Re(this);
	}
	run() {
		if (!(this.flags & 1)) return this.fn();
		this.flags |= 2, Ze(this), Ve(this);
		let e = A, t = qe;
		A = this, qe = !0;
		try {
			return this.fn();
		} finally {
			He(this), A = e, qe = t, this.flags &= -3;
		}
	}
	stop() {
		if (this.flags & 1) {
			for (let e = this.deps; e; e = e.nextDep) Ge(e);
			this.deps = this.depsTail = void 0, Ze(this), this.onStop && this.onStop(), this.flags &= -2;
		}
	}
	trigger() {
		this.flags & 64 ? Ne.add(this) : this.scheduler ? this.scheduler() : this.runIfDirty();
	}
	runIfDirty() {
		Ue(this) && this.run();
	}
	get dirty() {
		return Ue(this);
	}
}, Fe = 0, Ie, Le;
function Re(e, t = !1) {
	if (e.flags |= 8, t) {
		e.next = Le, Le = e;
		return;
	}
	e.next = Ie, Ie = e;
}
function ze() {
	Fe++;
}
function Be() {
	if (--Fe > 0) return;
	if (Le) {
		let e = Le;
		for (Le = void 0; e;) {
			let t = e.next;
			e.next = void 0, e.flags &= -9, e = t;
		}
	}
	let e;
	for (; Ie;) {
		let t = Ie;
		for (Ie = void 0; t;) {
			let n = t.next;
			if (t.next = void 0, t.flags &= -9, t.flags & 1) try {
				t.trigger();
			} catch (t) {
				e ||= t;
			}
			t = n;
		}
	}
	if (e) throw e;
}
function Ve(e) {
	for (let t = e.deps; t; t = t.nextDep) t.version = -1, t.prevActiveLink = t.dep.activeLink, t.dep.activeLink = t;
}
function He(e) {
	let t, n = e.depsTail, r = n;
	for (; r;) {
		let e = r.prevDep;
		r.version === -1 ? (r === n && (n = e), Ge(r), Ke(r)) : t = r, r.dep.activeLink = r.prevActiveLink, r.prevActiveLink = void 0, r = e;
	}
	e.deps = t, e.depsTail = n;
}
function Ue(e) {
	for (let t = e.deps; t; t = t.nextDep) if (t.dep.version !== t.version || t.dep.computed && (We(t.dep.computed) || t.dep.version !== t.version)) return !0;
	return !!e._dirty;
}
function We(e) {
	if (e.flags & 4 && !(e.flags & 16) || (e.flags &= -17, e.globalVersion === Qe) || (e.globalVersion = Qe, !e.isSSR && e.flags & 128 && (!e.deps && !e._dirty || !Ue(e)))) return;
	e.flags |= 2;
	let t = e.dep, n = A, r = qe;
	A = e, qe = !0;
	try {
		Ve(e);
		let n = e.fn(e._value);
		(t.version === 0 || se(n, e._value)) && (e.flags |= 128, e._value = n, t.version++);
	} catch (e) {
		throw t.version++, e;
	} finally {
		A = n, qe = r, He(e), e.flags &= -3;
	}
}
function Ge(e, t = !1) {
	let { dep: n, prevSub: r, nextSub: i } = e;
	if (r && (r.nextSub = i, e.prevSub = void 0), i && (i.prevSub = r, e.nextSub = void 0), n.subs === e && (n.subs = r, !r && n.computed)) {
		n.computed.flags &= -5;
		for (let e = n.computed.deps; e; e = e.nextDep) Ge(e, !0);
	}
	!t && !--n.sc && n.map && n.map.delete(n.key);
}
function Ke(e) {
	let { prevDep: t, nextDep: n } = e;
	t && (t.nextDep = n, e.prevDep = void 0), n && (n.prevDep = t, e.nextDep = void 0);
}
var qe = !0, Je = [];
function Ye() {
	Je.push(qe), qe = !1;
}
function Xe() {
	let e = Je.pop();
	qe = e === void 0 || e;
}
function Ze(e) {
	let { cleanup: t } = e;
	if (e.cleanup = void 0, t) {
		let e = A;
		A = void 0;
		try {
			t();
		} finally {
			A = e;
		}
	}
}
var Qe = 0, $e = class {
	constructor(e, t) {
		this.sub = e, this.dep = t, this.version = t.version, this.nextDep = this.prevDep = this.nextSub = this.prevSub = this.prevActiveLink = void 0;
	}
}, et = class {
	constructor(e) {
		this.computed = e, this.version = 0, this.activeLink = void 0, this.subs = void 0, this.map = void 0, this.key = void 0, this.sc = 0, this.__v_skip = !0;
	}
	track(e) {
		if (!A || !qe || A === this.computed) return;
		let t = this.activeLink;
		if (t === void 0 || t.sub !== A) t = this.activeLink = new $e(A, this), A.deps ? (t.prevDep = A.depsTail, A.depsTail.nextDep = t, A.depsTail = t) : A.deps = A.depsTail = t, tt(t);
		else if (t.version === -1 && (t.version = this.version, t.nextDep)) {
			let e = t.nextDep;
			e.prevDep = t.prevDep, t.prevDep && (t.prevDep.nextDep = e), t.prevDep = A.depsTail, t.nextDep = void 0, A.depsTail.nextDep = t, A.depsTail = t, A.deps === t && (A.deps = e);
		}
		return t;
	}
	trigger(e) {
		this.version++, Qe++, this.notify(e);
	}
	notify(e) {
		ze();
		try {
			for (let e = this.subs; e; e = e.prevSub) e.sub.notify() && e.sub.dep.notify();
		} finally {
			Be();
		}
	}
};
function tt(e) {
	if (e.dep.sc++, e.sub.flags & 4) {
		let t = e.dep.computed;
		if (t && !e.dep.subs) {
			t.flags |= 20;
			for (let e = t.deps; e; e = e.nextDep) tt(e);
		}
		let n = e.dep.subs;
		n !== e && (e.prevSub = n, n && (n.nextSub = e)), e.dep.subs = e;
	}
}
var nt = /* @__PURE__ */ new WeakMap(), rt = /* @__PURE__ */ Symbol(""), it = /* @__PURE__ */ Symbol(""), at = /* @__PURE__ */ Symbol("");
function j(e, t, n) {
	if (qe && A) {
		let t = nt.get(e);
		t || nt.set(e, t = /* @__PURE__ */ new Map());
		let r = t.get(n);
		r || (t.set(n, r = new et()), r.map = t, r.key = n), r.track();
	}
}
function ot(e, t, n, r, i, a) {
	let o = nt.get(e);
	if (!o) {
		Qe++;
		return;
	}
	let s = (e) => {
		e && e.trigger();
	};
	if (ze(), t === "clear") o.forEach(s);
	else {
		let i = f(e), a = i && ee(n);
		if (i && n === "length") {
			let e = Number(r);
			o.forEach((t, n) => {
				(n === "length" || n === at || !v(n) && n >= e) && s(t);
			});
		} else switch ((n !== void 0 || o.has(void 0)) && s(o.get(n)), a && s(o.get(at)), t) {
			case "add":
				i ? a && s(o.get("length")) : (s(o.get(rt)), p(e) && s(o.get(it)));
				break;
			case "delete":
				i || (s(o.get(rt)), p(e) && s(o.get(it)));
				break;
			case "set": p(e) && s(o.get(rt));
		}
	}
	Be();
}
function st(e) {
	let t = /* @__PURE__ */ M(e);
	return t === e || (j(t, "iterate", at), /* @__PURE__ */ Kt(e)) ? t : /* @__PURE__ */ Gt(e) ? /* @__PURE__ */ Wt(e) ? t.map((e) => Yt(N(e))) : t.map(Yt) : t.map(N);
}
function ct(e) {
	return j(e = /* @__PURE__ */ M(e), "iterate", at), e;
}
function lt(e, t) {
	return /* @__PURE__ */ Gt(e) ? Yt(/* @__PURE__ */ Wt(e) ? N(t) : t) : N(t);
}
var ut = {
	__proto__: null,
	[Symbol.iterator]() {
		return dt(this, Symbol.iterator, (e) => lt(this, e));
	},
	concat(...e) {
		return st(this).concat(...e.map((e) => f(e) ? st(e) : e));
	},
	entries() {
		return dt(this, "entries", (e) => (e[1] = lt(this, e[1]), e));
	},
	every(e, t) {
		return pt(this, "every", e, t, void 0, arguments);
	},
	filter(e, t) {
		return pt(this, "filter", e, t, (e) => e.map((e) => lt(this, e)), arguments);
	},
	find(e, t) {
		return pt(this, "find", e, t, (e) => lt(this, e), arguments);
	},
	findIndex(e, t) {
		return pt(this, "findIndex", e, t, void 0, arguments);
	},
	findLast(e, t) {
		return pt(this, "findLast", e, t, (e) => lt(this, e), arguments);
	},
	findLastIndex(e, t) {
		return pt(this, "findLastIndex", e, t, void 0, arguments);
	},
	forEach(e, t) {
		return pt(this, "forEach", e, t, void 0, arguments);
	},
	includes(...e) {
		return ht(this, "includes", e);
	},
	indexOf(...e) {
		return ht(this, "indexOf", e);
	},
	join(e) {
		return st(this).join(e);
	},
	lastIndexOf(...e) {
		return ht(this, "lastIndexOf", e);
	},
	map(e, t) {
		return pt(this, "map", e, t, void 0, arguments);
	},
	pop() {
		return gt(this, "pop");
	},
	push(...e) {
		return gt(this, "push", e);
	},
	reduce(e, ...t) {
		return mt(this, "reduce", e, t);
	},
	reduceRight(e, ...t) {
		return mt(this, "reduceRight", e, t);
	},
	shift() {
		return gt(this, "shift");
	},
	some(e, t) {
		return pt(this, "some", e, t, void 0, arguments);
	},
	splice(...e) {
		return gt(this, "splice", e);
	},
	toReversed() {
		return st(this).toReversed();
	},
	toSorted(e) {
		return st(this).toSorted(e);
	},
	toSpliced(...e) {
		return st(this).toSpliced(...e);
	},
	unshift(...e) {
		return gt(this, "unshift", e);
	},
	values() {
		return dt(this, "values", (e) => lt(this, e));
	}
};
function dt(e, t, n) {
	let r = ct(e), i = r[t]();
	return r !== e && !/* @__PURE__ */ Kt(e) && (i._next = i.next, i.next = () => {
		let e = i._next();
		return e.done || (e.value = n(e.value)), e;
	}), i;
}
var ft = Array.prototype;
function pt(e, t, n, r, i, a) {
	let o = ct(e), s = o !== e && !/* @__PURE__ */ Kt(e), c = o[t];
	if (c !== ft[t]) {
		let t = c.apply(e, a);
		return s ? N(t) : t;
	}
	let l = n;
	o !== e && (s ? l = function(t, r) {
		return n.call(this, lt(e, t), r, e);
	} : n.length > 2 && (l = function(t, r) {
		return n.call(this, t, r, e);
	}));
	let u = c.call(o, l, r);
	return s && i ? i(u) : u;
}
function mt(e, t, n, r) {
	let i = ct(e), a = i !== e && !/* @__PURE__ */ Kt(e), o = n, s = !1;
	i !== e && (a ? (s = r.length === 0, o = function(t, r, i) {
		return s && (s = !1, t = lt(e, t)), n.call(this, t, lt(e, r), i, e);
	}) : n.length > 3 && (o = function(t, r, i) {
		return n.call(this, t, r, i, e);
	}));
	let c = i[t](o, ...r);
	return s ? lt(e, c) : c;
}
function ht(e, t, n) {
	let r = /* @__PURE__ */ M(e);
	j(r, "iterate", at);
	let i = r[t](...n);
	return (i === -1 || i === !1) && /* @__PURE__ */ qt(n[0]) ? (n[0] = /* @__PURE__ */ M(n[0]), r[t](...n)) : i;
}
function gt(e, t, n = []) {
	Ye(), ze();
	let r = (/* @__PURE__ */ M(e))[t].apply(e, n);
	return Be(), Xe(), r;
}
var _t = /* @__PURE__ */ t("__proto__,__v_isRef,__isVue"), vt = new Set(/* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((e) => e !== "arguments" && e !== "caller").map((e) => Symbol[e]).filter(v));
function yt(e) {
	v(e) || (e = String(e));
	let t = /* @__PURE__ */ M(this);
	return j(t, "has", e), t.hasOwnProperty(e);
}
var bt = class {
	constructor(e = !1, t = !1) {
		this._isReadonly = e, this._isShallow = t;
	}
	get(e, t, n) {
		if (t === "__v_skip") return e.__v_skip;
		let r = this._isReadonly, i = this._isShallow;
		if (t === "__v_isReactive") return !r;
		if (t === "__v_isReadonly") return r;
		if (t === "__v_isShallow") return i;
		if (t === "__v_raw") return n === (r ? i ? Rt : Lt : i ? It : Ft).get(e) || Object.getPrototypeOf(e) === Object.getPrototypeOf(n) ? e : void 0;
		let a = f(e);
		if (!r) {
			let e;
			if (a && (e = ut[t])) return e;
			if (t === "hasOwnProperty") return yt;
		}
		let o = Reflect.get(e, t, /* @__PURE__ */ P(e) ? e : n);
		if ((v(t) ? vt.has(t) : _t(t)) || (r || j(e, "get", t), i)) return o;
		if (/* @__PURE__ */ P(o)) {
			let e = a && ee(t) ? o : o.value;
			return r && y(e) ? /* @__PURE__ */ Ht(e) : e;
		}
		return y(o) ? r ? /* @__PURE__ */ Ht(o) : /* @__PURE__ */ Bt(o) : o;
	}
}, xt = class extends bt {
	constructor(e = !1) {
		super(!1, e);
	}
	set(e, t, n, r) {
		let i = e[t], a = f(e) && ee(t);
		if (!this._isShallow) {
			let e = /* @__PURE__ */ Gt(i);
			if (!/* @__PURE__ */ Kt(n) && !/* @__PURE__ */ Gt(n) && (i = /* @__PURE__ */ M(i), n = /* @__PURE__ */ M(n)), !a && /* @__PURE__ */ P(i) && !/* @__PURE__ */ P(n)) return e || (i.value = n), !0;
		}
		let o = a ? Number(t) < e.length : d(e, t), s = Reflect.set(e, t, n, /* @__PURE__ */ P(e) ? e : r);
		return e === /* @__PURE__ */ M(r) && s && (o ? se(n, i) && ot(e, "set", t, n, i) : ot(e, "add", t, n)), s;
	}
	deleteProperty(e, t) {
		let n = d(e, t), r = e[t], i = Reflect.deleteProperty(e, t);
		return i && n && ot(e, "delete", t, void 0, r), i;
	}
	has(e, t) {
		let n = Reflect.has(e, t);
		return (!v(t) || !vt.has(t)) && j(e, "has", t), n;
	}
	ownKeys(e) {
		return j(e, "iterate", f(e) ? "length" : rt), Reflect.ownKeys(e);
	}
}, St = class extends bt {
	constructor(e = !1) {
		super(!0, e);
	}
	set(e, t) {
		return !0;
	}
	deleteProperty(e, t) {
		return !0;
	}
}, Ct = /* @__PURE__ */ new xt(), wt = /* @__PURE__ */ new St(), Tt = /* @__PURE__ */ new xt(!0), Et = (e) => e, Dt = (e) => Reflect.getPrototypeOf(e);
function Ot(e, t, n) {
	return function(...r) {
		let i = this.__v_raw, a = /* @__PURE__ */ M(i), o = p(a), s = e === "entries" || e === Symbol.iterator && o, l = e === "keys" && o, u = i[e](...r), d = n ? Et : t ? Yt : N;
		return !t && j(a, "iterate", l ? it : rt), c(Object.create(u), { next() {
			let { value: e, done: t } = u.next();
			return t ? {
				value: e,
				done: t
			} : {
				value: s ? [d(e[0]), d(e[1])] : d(e),
				done: t
			};
		} });
	};
}
function kt(e) {
	return function(...t) {
		return e === "delete" ? !1 : e === "clear" ? void 0 : this;
	};
}
function At(e, t) {
	let n = {
		get(n) {
			let r = this.__v_raw, i = /* @__PURE__ */ M(r), a = /* @__PURE__ */ M(n);
			e || (se(n, a) && j(i, "get", n), j(i, "get", a));
			let { has: o } = Dt(i), s = t ? Et : e ? Yt : N;
			if (o.call(i, n)) return s(r.get(n));
			if (o.call(i, a)) return s(r.get(a));
			r !== i && r.get(n);
		},
		get size() {
			let t = this.__v_raw;
			return !e && j(/* @__PURE__ */ M(t), "iterate", rt), t.size;
		},
		has(t) {
			let n = this.__v_raw, r = /* @__PURE__ */ M(n), i = /* @__PURE__ */ M(t);
			return e || (se(t, i) && j(r, "has", t), j(r, "has", i)), t === i ? n.has(t) : n.has(t) || n.has(i);
		},
		forEach(n, r) {
			let i = this, a = i.__v_raw, o = /* @__PURE__ */ M(a), s = t ? Et : e ? Yt : N;
			return !e && j(o, "iterate", rt), a.forEach((e, t) => n.call(r, s(e), s(t), i));
		}
	};
	return c(n, e ? {
		add: kt("add"),
		set: kt("set"),
		delete: kt("delete"),
		clear: kt("clear")
	} : {
		add(e) {
			let n = /* @__PURE__ */ M(this), r = Dt(n), i = /* @__PURE__ */ M(e), a = !t && !/* @__PURE__ */ Kt(e) && !/* @__PURE__ */ Gt(e) ? i : e;
			return r.has.call(n, a) || se(e, a) && r.has.call(n, e) || se(i, a) && r.has.call(n, i) || (n.add(a), ot(n, "add", a, a)), this;
		},
		set(e, n) {
			!t && !/* @__PURE__ */ Kt(n) && !/* @__PURE__ */ Gt(n) && (n = /* @__PURE__ */ M(n));
			let r = /* @__PURE__ */ M(this), { has: i, get: a } = Dt(r), o = i.call(r, e);
			o ||= (e = /* @__PURE__ */ M(e), i.call(r, e));
			let s = a.call(r, e);
			return r.set(e, n), o ? se(n, s) && ot(r, "set", e, n, s) : ot(r, "add", e, n), this;
		},
		delete(e) {
			let t = /* @__PURE__ */ M(this), { has: n, get: r } = Dt(t), i = n.call(t, e);
			i ||= (e = /* @__PURE__ */ M(e), n.call(t, e));
			let a = r ? r.call(t, e) : void 0, o = t.delete(e);
			return i && ot(t, "delete", e, void 0, a), o;
		},
		clear() {
			let e = /* @__PURE__ */ M(this), t = e.size !== 0, n = e.clear();
			return t && ot(e, "clear", void 0, void 0, void 0), n;
		}
	}), [
		"keys",
		"values",
		"entries",
		Symbol.iterator
	].forEach((r) => {
		n[r] = Ot(r, e, t);
	}), n;
}
function jt(e, t) {
	let n = At(e, t);
	return (t, r, i) => r === "__v_isReactive" ? !e : r === "__v_isReadonly" ? e : r === "__v_raw" ? t : Reflect.get(d(n, r) && r in t ? n : t, r, i);
}
var Mt = { get: /* @__PURE__ */ jt(!1, !1) }, Nt = { get: /* @__PURE__ */ jt(!1, !0) }, Pt = { get: /* @__PURE__ */ jt(!0, !1) }, Ft = /* @__PURE__ */ new WeakMap(), It = /* @__PURE__ */ new WeakMap(), Lt = /* @__PURE__ */ new WeakMap(), Rt = /* @__PURE__ */ new WeakMap();
function zt(e) {
	switch (e) {
		case "Object":
		case "Array": return 1;
		case "Map":
		case "Set":
		case "WeakMap":
		case "WeakSet": return 2;
		default: return 0;
	}
}
// @__NO_SIDE_EFFECTS__
function Bt(e) {
	return /* @__PURE__ */ Gt(e) ? e : Ut(e, !1, Ct, Mt, Ft);
}
// @__NO_SIDE_EFFECTS__
function Vt(e) {
	return Ut(e, !1, Tt, Nt, It);
}
// @__NO_SIDE_EFFECTS__
function Ht(e) {
	return Ut(e, !0, wt, Pt, Lt);
}
function Ut(e, t, n, r, i) {
	if (!y(e) || e.__v_raw && !(t && e.__v_isReactive) || e.__v_skip || !Object.isExtensible(e)) return e;
	let a = i.get(e);
	if (a) return a;
	let o = zt(C(e));
	if (o === 0) return e;
	let s = new Proxy(e, o === 2 ? r : n);
	return i.set(e, s), s;
}
// @__NO_SIDE_EFFECTS__
function Wt(e) {
	return /* @__PURE__ */ Gt(e) ? /* @__PURE__ */ Wt(e.__v_raw) : !!(e && e.__v_isReactive);
}
// @__NO_SIDE_EFFECTS__
function Gt(e) {
	return !!(e && e.__v_isReadonly);
}
// @__NO_SIDE_EFFECTS__
function Kt(e) {
	return !!(e && e.__v_isShallow);
}
// @__NO_SIDE_EFFECTS__
function qt(e) {
	return e ? !!e.__v_raw : !1;
}
// @__NO_SIDE_EFFECTS__
function M(e) {
	let t = e && e.__v_raw;
	return t ? /* @__PURE__ */ M(t) : e;
}
function Jt(e) {
	return !d(e, "__v_skip") && Object.isExtensible(e) && ce(e, "__v_skip", !0), e;
}
var N = (e) => y(e) ? /* @__PURE__ */ Bt(e) : e, Yt = (e) => y(e) ? /* @__PURE__ */ Ht(e) : e;
// @__NO_SIDE_EFFECTS__
function P(e) {
	return e ? e.__v_isRef === !0 : !1;
}
// @__NO_SIDE_EFFECTS__
function Xt(e) {
	return Qt(e, !1);
}
// @__NO_SIDE_EFFECTS__
function Zt(e) {
	return Qt(e, !0);
}
function Qt(e, t) {
	return /* @__PURE__ */ P(e) ? e : new $t(e, t);
}
var $t = class {
	constructor(e, t) {
		this.dep = new et(), this.__v_isRef = !0, this.__v_isShallow = !1, this._rawValue = t ? e : /* @__PURE__ */ M(e), this._value = t ? e : N(e), this.__v_isShallow = t;
	}
	get value() {
		return this.dep.track(), this._value;
	}
	set value(e) {
		let t = this._rawValue, n = this.__v_isShallow || /* @__PURE__ */ Kt(e) || /* @__PURE__ */ Gt(e);
		e = n ? e : /* @__PURE__ */ M(e), se(e, t) && (this._rawValue = e, this._value = n ? e : N(e), this.dep.trigger());
	}
};
function F(e) {
	return /* @__PURE__ */ P(e) ? e.value : e;
}
var en = {
	get: (e, t, n) => t === "__v_raw" ? e : F(Reflect.get(e, t, n)),
	set: (e, t, n, r) => {
		let i = e[t];
		return /* @__PURE__ */ P(i) && !/* @__PURE__ */ P(n) ? (i.value = n, !0) : Reflect.set(e, t, n, r);
	}
};
function tn(e) {
	return /* @__PURE__ */ Wt(e) ? e : new Proxy(e, en);
}
var nn = class {
	constructor(e, t, n) {
		this.fn = e, this.setter = t, this._value = void 0, this.dep = new et(this), this.__v_isRef = !0, this.deps = void 0, this.depsTail = void 0, this.flags = 16, this.globalVersion = Qe - 1, this.next = void 0, this.effect = this, this.__v_isReadonly = !t, this.isSSR = n;
	}
	notify() {
		if (this.flags |= 16, !(this.flags & 8) && A !== this) return Re(this, !0), !0;
	}
	get value() {
		let e = this.dep.track();
		return We(this), e && (e.version = this.dep.version), this._value;
	}
	set value(e) {
		this.setter && this.setter(e);
	}
};
// @__NO_SIDE_EFFECTS__
function rn(e, t, n = !1) {
	let r, i;
	return g(e) ? r = e : (r = e.get, i = e.set), new nn(r, i, n);
}
var an = {}, on = /* @__PURE__ */ new WeakMap(), sn = void 0;
function cn(e, t = !1, n = sn) {
	if (n) {
		let t = on.get(n);
		t || on.set(n, t = []), t.push(e);
	}
}
function ln(e, t, r = n) {
	let { immediate: a, deep: o, once: s, scheduler: c, augmentJob: u, call: d } = r, p = (e) => o ? e : /* @__PURE__ */ Kt(e) || o === !1 || o === 0 ? un(e, 1) : un(e), m, h, _, v, y = !1, b = !1;
	if (/* @__PURE__ */ P(e) ? (h = () => e.value, y = /* @__PURE__ */ Kt(e)) : /* @__PURE__ */ Wt(e) ? (h = () => p(e), y = !0) : f(e) ? (b = !0, y = e.some((e) => /* @__PURE__ */ Wt(e) || /* @__PURE__ */ Kt(e)), h = () => e.map((e) => {
		if (/* @__PURE__ */ P(e)) return e.value;
		if (/* @__PURE__ */ Wt(e)) return p(e);
		if (g(e)) return d ? d(e, 2) : e();
	})) : h = g(e) ? t ? d ? () => d(e, 2) : e : () => {
		if (_) {
			Ye();
			try {
				_();
			} finally {
				Xe();
			}
		}
		let t = sn;
		sn = m;
		try {
			return d ? d(e, 3, [v]) : e(v);
		} finally {
			sn = t;
		}
	} : i, t && o) {
		let e = h, t = o === !0 ? Infinity : o;
		h = () => un(e(), t);
	}
	let x = je(), S = () => {
		m.stop(), x && x.active && l(x.effects, m);
	};
	if (s && t) {
		let e = t;
		t = (...t) => {
			let n = e(...t);
			return S(), n;
		};
	}
	let C = b ? Array(e.length).fill(an) : an, w = (e) => {
		if (m.flags & 1 && (m.dirty || e)) {
			if (t) {
				let n = m.run();
				if (e || o || y || (b ? n.some((e, t) => se(e, C[t])) : se(n, C))) {
					_ && _();
					let e = sn;
					sn = m;
					try {
						let e = [
							n,
							C === an ? void 0 : b && C[0] === an ? [] : C,
							v
						];
						C = n, d ? d(t, 3, e) : t(...e);
					} finally {
						sn = e;
					}
				}
			} else m.run();
		}
	};
	return u && u(w), m = new Pe(h), m.scheduler = c ? () => c(w, !1) : w, v = (e) => cn(e, !1, m), _ = m.onStop = () => {
		let e = on.get(m);
		if (e) {
			if (d) d(e, 4);
			else for (let t of e) t();
			on.delete(m);
		}
	}, t ? a ? w(!0) : C = m.run() : c ? c(w.bind(null, !0), !0) : m.run(), S.pause = m.pause.bind(m), S.resume = m.resume.bind(m), S.stop = S, S;
}
function un(e, t = Infinity, n) {
	if (t <= 0 || !y(e) || e.__v_skip || (n ||= /* @__PURE__ */ new Map(), (n.get(e) || 0) >= t)) return e;
	if (n.set(e, t), t--, /* @__PURE__ */ P(e)) un(e.value, t, n);
	else if (f(e)) for (let r = 0; r < e.length; r++) un(e[r], t, n);
	else if (m(e) || p(e)) e.forEach((e) => {
		un(e, t, n);
	});
	else if (w(e)) {
		for (let r in e) un(e[r], t, n);
		for (let r of Object.getOwnPropertySymbols(e)) Object.prototype.propertyIsEnumerable.call(e, r) && un(e[r], t, n);
	}
	return e;
}
//#endregion
//#region ../../node_modules/@vue/runtime-core/dist/runtime-core.esm-bundler.js
function dn(e, t, n, r) {
	try {
		return r ? e(...r) : e();
	} catch (e) {
		pn(e, t, n);
	}
}
function fn(e, t, n, r) {
	if (g(e)) {
		let i = dn(e, t, n, r);
		return i && b(i) && i.catch((e) => {
			pn(e, t, n);
		}), i;
	}
	if (f(e)) {
		let i = [];
		for (let a = 0; a < e.length; a++) i.push(fn(e[a], t, n, r));
		return i;
	}
}
function pn(e, t, r, i = !0) {
	let a = t ? t.vnode : null, { errorHandler: o, throwUnhandledErrorInProduction: s } = t && t.appContext.config || n;
	if (t) {
		let n = t.parent, i = t.proxy, a = `https://vuejs.org/error-reference/#runtime-${r}`;
		for (; n;) {
			let t = n.ec;
			if (t) {
				for (let n = 0; n < t.length; n++) if (t[n](e, i, a) === !1) return;
			}
			n = n.parent;
		}
		if (o) {
			Ye(), dn(o, null, 10, [
				e,
				i,
				a
			]), Xe();
			return;
		}
	}
	mn(e, r, a, i, s);
}
function mn(e, t, n, r = !0, i = !1) {
	if (i) throw e;
	console.error(e);
}
var I = [], hn = -1, gn = [], _n = null, vn = 0, yn = /* @__PURE__ */ Promise.resolve(), bn = null;
function xn(e) {
	let t = bn || yn;
	return e ? t.then(this ? e.bind(this) : e) : t;
}
function Sn(e) {
	let t = hn + 1, n = I.length;
	for (; t < n;) {
		let r = t + n >>> 1, i = I[r], a = On(i);
		a < e || a === e && i.flags & 2 ? t = r + 1 : n = r;
	}
	return t;
}
function Cn(e) {
	if (!(e.flags & 1)) {
		let t = On(e), n = I[I.length - 1];
		!n || !(e.flags & 2) && t >= On(n) ? I.push(e) : I.splice(Sn(t), 0, e), e.flags |= 1, wn();
	}
}
function wn() {
	bn ||= yn.then(kn);
}
function Tn(e) {
	if (!f(e)) _n && e.id === -1 ? _n.splice(vn + 1, 0, e) : e.flags & 1 || (gn.push(e), e.flags |= 1);
	else for (let t = 0; t < e.length; t++) gn.push(e[t]);
	wn();
}
function En(e, t, n = hn + 1) {
	for (; n < I.length; n++) {
		let t = I[n];
		if (t && t.flags & 2) {
			if (e && t.id !== e.uid) continue;
			I.splice(n, 1), n--, t.flags & 4 && (t.flags &= -2), t(), t.flags & 4 || (t.flags &= -2);
		}
	}
}
function Dn(e) {
	if (gn.length) {
		let e = [...new Set(gn)].sort((e, t) => On(e) - On(t));
		if (gn.length = 0, _n) {
			for (let t = 0; t < e.length; t++) _n.push(e[t]);
			return;
		}
		for (_n = e, vn = 0; vn < _n.length; vn++) {
			let e = _n[vn];
			e.flags & 4 && (e.flags &= -2), e.flags & 8 || e(), e.flags &= -2;
		}
		_n = null, vn = 0;
	}
}
var On = (e) => e.id == null ? e.flags & 2 ? -1 : Infinity : e.id;
function kn(e) {
	try {
		for (hn = 0; hn < I.length; hn++) {
			let e = I[hn];
			e && !(e.flags & 8) && (e.flags & 4 && (e.flags &= -2), dn(e, e.i, e.i ? 15 : 14), e.flags & 4 || (e.flags &= -2));
		}
	} finally {
		for (; hn < I.length; hn++) {
			let e = I[hn];
			e && (e.flags &= -2);
		}
		hn = -1, I.length = 0, Dn(e), bn = null, (I.length || gn.length) && kn(e);
	}
}
var L = null, An = null;
function jn(e) {
	let t = L;
	return L = e, An = e && e.type.__scopeId || null, t;
}
function R(e, t = L, n) {
	if (!t || e._n) return e;
	let r = (...n) => {
		r._d && Ii(-1);
		let i = jn(t), a = Ni.length, o;
		try {
			o = e(...n);
		} finally {
			for (let e = Ni.length; e > a; e--) Pi();
			jn(i), r._d && Ii(1);
		}
		return o;
	};
	return r._n = !0, r._c = !0, r._d = !0, r;
}
function Mn(e, t, n, r) {
	let i = e.dirs, a = t && t.dirs;
	for (let o = 0; o < i.length; o++) {
		let s = i[o];
		a && (s.oldValue = a[o].value);
		let c = s.dir[r];
		c && (Ye(), fn(c, n, 8, [
			e.el,
			s,
			e,
			t
		]), Xe());
	}
}
function Nn(e, t) {
	if (Q) {
		let n = Q.provides, r = Q.parent && Q.parent.provides;
		r === n && (n = Q.provides = Object.create(r)), n[e] = t;
	}
}
function Pn(e, t, n = !1) {
	let r = $i();
	if (r || Vr) {
		let i = Vr ? Vr._context.provides : r ? r.parent == null || r.ce ? r.vnode.appContext && r.vnode.appContext.provides : r.parent.provides : void 0;
		if (i && e in i) return i[e];
		if (arguments.length > 1) return n && g(t) ? t.call(r && r.proxy) : t;
	}
}
var Fn = /* @__PURE__ */ Symbol.for("v-scx"), In = () => Pn(Fn);
function Ln(e, t, n) {
	return Rn(e, t, n);
}
function Rn(e, t, r = n) {
	let { immediate: a, deep: o, flush: s, once: l } = r, u = c({}, r), d = t && a || !t && s !== "post", f;
	if (aa) {
		if (s === "sync") {
			let e = In();
			f = e.__watcherHandles ||= [];
		} else if (!d) {
			let e = () => {};
			return e.stop = i, e.resume = i, e.pause = i, e;
		}
	}
	let p = Q;
	u.call = (e, t, n) => fn(e, p, t, n);
	let m = !1;
	s === "post" ? u.scheduler = (e) => {
		H(e, p && p.suspense);
	} : s !== "sync" && (m = !0, u.scheduler = (e, t) => {
		t ? e() : Cn(e);
	}), u.augmentJob = (e) => {
		t && (e.flags |= 4), m && (e.flags |= 2, p && (e.id = p.uid, e.i = p));
	};
	let h = ln(e, t, u);
	return aa && (f ? f.push(h) : d && h()), h;
}
function zn(e, t, n) {
	let r = this.proxy, i = _(e) ? e.includes(".") ? Bn(r, e) : () => r[e] : e.bind(r, r), a;
	g(t) ? a = t : (a = t.handler, n = t);
	let o = na(this), s = Rn(i, a.bind(r), n);
	return o(), s;
}
function Bn(e, t) {
	let n = t.split(".");
	return () => {
		let t = e;
		for (let e = 0; e < n.length && t; e++) t = t[n[e]];
		return t;
	};
}
var Vn = /* @__PURE__ */ Symbol("_vte"), Hn = (e) => e.__isTeleport, Un = /* @__PURE__ */ Symbol("_leaveCb");
function Wn(e) {
	let t = e[0];
	if (e.length > 1) {
		for (let n of e) if (n.type !== ji) {
			t = n;
			break;
		}
	}
	return t;
}
function Gn(e) {
	if (!$n(e)) return Hn(e.type) && e.children ? Wn(e.children) : e;
	if (e.component) return e.component.subTree;
	let { shapeFlag: t, children: n } = e;
	if (n) {
		if (t & 16) return n[0];
		if (t & 32 && g(n.default)) return n.default();
	}
}
function Kn(e, t) {
	if (e.shapeFlag & 6 && e.component) {
		e.transition = t;
		let n = e.component.subTree;
		Kn(Hn(n.type) && Gn(n) || n, t);
	} else e.shapeFlag & 128 ? (e.ssContent.transition = t.clone(e.ssContent), e.ssFallback.transition = t.clone(e.ssFallback)) : e.transition = t;
}
// @__NO_SIDE_EFFECTS__
function z(e, t) {
	return g(e) ? /* @__PURE__ */ c({ name: e.name }, t, { setup: e }) : e;
}
function qn(e) {
	e.ids = [
		e.ids[0] + e.ids[2]++ + "-",
		0,
		0
	];
}
function Jn(e, t) {
	let n;
	return !!((n = Object.getOwnPropertyDescriptor(e, t)) && !n.configurable);
}
var Yn = /* @__PURE__ */ new WeakMap();
function Xn(e, t, r, i, o = !1) {
	if (f(e)) {
		e.forEach((e, n) => Xn(e, t && (f(t) ? t[n] : t), r, i, o));
		return;
	}
	if (Qn(i) && !o) {
		i.shapeFlag & 512 && i.type.__asyncResolved && i.component.subTree.component && Xn(e, t, r, i.component.subTree);
		return;
	}
	let s = i.shapeFlag & 4 ? fa(i.component) : i.el, c = o ? null : s, { i: u, r: p } = e, m = t && t.r, h = u.refs === n ? u.refs = {} : u.refs, v = u.setupState, y = /* @__PURE__ */ M(v), b = v === n ? a : (e) => !Jn(h, e) && d(y, e), x = (e, t) => !(t && Jn(h, t));
	if (m != null && m !== p) {
		if (Zn(t), _(m)) h[m] = null, b(m) && (v[m] = null);
		else if (/* @__PURE__ */ P(m)) {
			let e = t;
			x(m, e.k) && (m.value = null), e.k && (h[e.k] = null);
		}
	}
	if (g(p)) dn(p, u, 12, [c, h]);
	else {
		let t = _(p), n = /* @__PURE__ */ P(p);
		if (t || n) {
			let i = () => {
				if (e.f) {
					let n = t ? b(p) ? v[p] : h[p] : x(p) || !e.k ? p.value : h[e.k];
					if (o) f(n) && l(n, s);
					else if (f(n)) n.includes(s) || n.push(s);
					else if (t) h[p] = [s], b(p) && (v[p] = h[p]);
					else {
						let t = [s];
						x(p, e.k) && (p.value = t), e.k && (h[e.k] = t);
					}
				} else t ? (h[p] = c, b(p) && (v[p] = c)) : n && (x(p, e.k) && (p.value = c), e.k && (h[e.k] = c));
			};
			if (c) {
				let t = () => {
					i(), Yn.delete(e);
				};
				t.id = -1, Yn.set(e, t), H(t, r);
			} else Zn(e), i();
		}
	}
}
function Zn(e) {
	let t = Yn.get(e);
	t && (t.flags |= 8, Yn.delete(e));
}
fe().requestIdleCallback, fe().cancelIdleCallback;
var Qn = (e) => !!e.type.__asyncLoader, $n = (e) => e.type.__isKeepAlive;
function er(e, t) {
	nr(e, "a", t);
}
function tr(e, t) {
	nr(e, "da", t);
}
function nr(e, t, n = Q) {
	let r = e.__wdc ||= () => {
		let t = n;
		for (; t;) {
			if (t.isDeactivated) return;
			t = t.parent;
		}
		return e();
	};
	if (ir(t, r, n), n) {
		let e = n.parent;
		for (; e && e.parent;) $n(e.parent.vnode) && rr(r, t, n, e), e = e.parent;
	}
}
function rr(e, t, n, r) {
	let i = ir(t, e, r, !0);
	dr(() => {
		l(r[t], i);
	}, n);
}
function ir(e, t, n = Q, r = !1) {
	if (n) {
		let i = n[e] || (n[e] = []), a = t.__weh ||= (...r) => {
			Ye();
			let i = na(n), a = fn(t, n, e, r);
			return i(), Xe(), a;
		};
		return r ? i.unshift(a) : i.push(a), a;
	}
}
var ar = (e) => (t, n = Q) => {
	(!aa || e === "sp") && ir(e, (...e) => t(...e), n);
}, or = ar("bm"), sr = ar("m"), cr = ar("bu"), lr = ar("u"), ur = ar("bum"), dr = ar("um"), fr = ar("sp"), pr = ar("rtg"), mr = ar("rtc");
function hr(e, t = Q) {
	ir("ec", e, t);
}
var gr = /* @__PURE__ */ Symbol.for("v-ndc");
function B(e, t, n, r) {
	let i, a = n && n[r], o = f(e);
	if (o || _(e)) {
		let n = o && /* @__PURE__ */ Wt(e), r = !1, s = !1;
		n && (r = !/* @__PURE__ */ Kt(e), s = /* @__PURE__ */ Gt(e), e = ct(e)), i = Array(e.length);
		for (let n = 0, o = e.length; n < o; n++) i[n] = t(r ? s ? Yt(N(e[n])) : N(e[n]) : e[n], n, void 0, a && a[n]);
	} else if (typeof e == "number") {
		i = Array(e);
		for (let n = 0; n < e; n++) i[n] = t(n + 1, n, void 0, a && a[n]);
	} else if (y(e)) {
		if (e[Symbol.iterator]) i = Array.from(e, (e, n) => t(e, n, void 0, a && a[n]));
		else {
			let n = Object.keys(e);
			i = Array(n.length);
			for (let r = 0, o = n.length; r < o; r++) {
				let o = n[r];
				i[r] = t(e[o], o, r, a && a[r]);
			}
		}
	} else i = [];
	return n && (n[r] = i), i;
}
function _r(e, t, n, r, i, a) {
	if (n ??= {}, L.ce || L.parent && Qn(L.parent) && L.parent.ce) {
		let e = a != null && n.key == null ? c({}, n, { key: a }) : n, i = Object.keys(e).length > 0;
		return t !== "default" && (e.name = t), G(), q(U, null, [Y("slot", e, r && r())], i ? -2 : 64);
	}
	let o = e[t];
	o && o._c && (o._d = !1);
	let s = Ni.length;
	G();
	let l;
	try {
		let i = o && vr(o(n)), s = n.key || a || i && i.key;
		l = q(U, { key: (s && !v(s) ? s : `_${t}`) + (!i && r ? "_fb" : "") }, i || (r ? r() : []), i && e._ === 1 ? 64 : -2);
	} catch (e) {
		for (let e = Ni.length; e > s; e--) Pi();
		throw e;
	} finally {
		o && o._c && (o._d = !0);
	}
	return !i && l.scopeId && (l.slotScopeIds = [l.scopeId + "-s"]), l;
}
function vr(e) {
	return e.some((e) => !Ri(e) || !(e.type === ji || e.type === U && !vr(e.children))) ? e : null;
}
var yr = (e) => e ? ia(e) ? fa(e) : yr(e.parent) : null, br = /* @__PURE__ */ c(/* @__PURE__ */ Object.create(null), {
	$: (e) => e,
	$el: (e) => e.vnode.el,
	$data: (e) => e.data,
	$props: (e) => e.props,
	$attrs: (e) => e.attrs,
	$slots: (e) => e.slots,
	$refs: (e) => e.refs,
	$parent: (e) => yr(e.parent),
	$root: (e) => yr(e.root),
	$host: (e) => e.ce,
	$emit: (e) => e.emit,
	$options: (e) => kr(e),
	$forceUpdate: (e) => e.f ||= () => {
		Cn(e.update);
	},
	$nextTick: (e) => e.n ||= xn.bind(e.proxy),
	$watch: (e) => zn.bind(e)
}), xr = (e, t) => e !== n && !e.__isScriptSetup && d(e, t), Sr = {
	get({ _: e }, t) {
		if (t === "__v_skip") return !0;
		let { ctx: r, setupState: i, data: a, props: o, accessCache: s, type: c, appContext: l } = e;
		if (t[0] !== "$") {
			let e = s[t];
			if (e !== void 0) switch (e) {
				case 1: return i[t];
				case 2: return a[t];
				case 4: return r[t];
				case 3: return o[t];
			}
			else if (xr(i, t)) return s[t] = 1, i[t];
			else if (a !== n && d(a, t)) return s[t] = 2, a[t];
			else if (d(o, t)) return s[t] = 3, o[t];
			else if (r !== n && d(r, t)) return s[t] = 4, r[t];
			else wr && (s[t] = 0);
		}
		let u = br[t], f, p;
		if (u) return t === "$attrs" && j(e.attrs, "get", ""), u(e);
		if ((f = c.__cssModules) && (f = f[t])) return f;
		if (r !== n && d(r, t)) return s[t] = 4, r[t];
		if (p = l.config.globalProperties, d(p, t)) return p[t];
	},
	set({ _: e }, t, r) {
		let { data: i, setupState: a, ctx: o } = e;
		return xr(a, t) ? (a[t] = r, !0) : i !== n && d(i, t) ? (i[t] = r, !0) : d(e.props, t) || t[0] === "$" && t.slice(1) in e ? !1 : (o[t] = r, !0);
	},
	has({ _: { data: e, setupState: t, accessCache: r, ctx: i, appContext: a, props: o, type: s } }, c) {
		let l;
		return !!(r[c] || e !== n && c[0] !== "$" && d(e, c) || xr(t, c) || d(o, c) || d(i, c) || d(br, c) || d(a.config.globalProperties, c) || (l = s.__cssModules) && l[c]);
	},
	defineProperty(e, t, n) {
		return n.get == null ? d(n, "value") && this.set(e, t, n.value, null) : e._.accessCache[t] = 0, Reflect.defineProperty(e, t, n);
	}
};
function Cr(e) {
	return f(e) ? e.reduce((e, t) => (e[t] = null, e), {}) : e;
}
var wr = !0;
function Tr(e) {
	let t = kr(e), n = e.proxy, r = e.ctx;
	wr = !1, t.beforeCreate && Dr(t.beforeCreate, e, "bc");
	let { data: a, computed: o, methods: s, watch: c, provide: l, inject: u, created: d, beforeMount: p, mounted: m, beforeUpdate: h, updated: _, activated: v, deactivated: b, beforeDestroy: x, beforeUnmount: S, destroyed: C, unmounted: w, render: ee, renderTracked: te, renderTriggered: ne, errorCaptured: re, serverPrefetch: T, expose: ie, inheritAttrs: E, components: ae, directives: oe, filters: se } = t;
	if (u && Er(u, r, null), s) for (let e in s) {
		let t = s[e];
		g(t) && (r[e] = t.bind(n));
	}
	if (a) {
		let t = a.call(n, n);
		y(t) && (e.data = /* @__PURE__ */ Bt(t));
	}
	if (wr = !0, o) for (let e in o) {
		let t = o[e], a = $({
			get: g(t) ? t.bind(n, n) : g(t.get) ? t.get.bind(n, n) : i,
			set: !g(t) && g(t.set) ? t.set.bind(n) : i
		});
		Object.defineProperty(r, e, {
			enumerable: !0,
			configurable: !0,
			get: () => a.value,
			set: (e) => a.value = e
		});
	}
	if (c) for (let e in c) Or(c[e], r, n, e);
	if (l) {
		let e = g(l) ? l.call(n) : l;
		Reflect.ownKeys(e).forEach((t) => {
			Nn(t, e[t]);
		});
	}
	d && Dr(d, e, "c");
	function D(e, t) {
		f(t) ? t.forEach((t) => e(t.bind(n))) : t && e(t.bind(n));
	}
	if (D(or, p), D(sr, m), D(cr, h), D(lr, _), D(er, v), D(tr, b), D(hr, re), D(mr, te), D(pr, ne), D(ur, S), D(dr, w), D(fr, T), f(ie)) {
		if (ie.length) {
			let t = e.exposed ||= {};
			ie.forEach((e) => {
				Object.defineProperty(t, e, {
					get: () => n[e],
					set: (t) => n[e] = t,
					enumerable: !0
				});
			});
		} else e.exposed ||= {};
	}
	ee && e.render === i && (e.render = ee), E != null && (e.inheritAttrs = E), ae && (e.components = ae), oe && (e.directives = oe), T && qn(e);
}
function Er(e, t, n = i) {
	f(e) && (e = Pr(e));
	for (let n in e) {
		let r = e[n], i;
		i = y(r) ? "default" in r ? Pn(r.from || n, r.default, !0) : Pn(r.from || n) : Pn(r), /* @__PURE__ */ P(i) ? Object.defineProperty(t, n, {
			enumerable: !0,
			configurable: !0,
			get: () => i.value,
			set: (e) => i.value = e
		}) : t[n] = i;
	}
}
function Dr(e, t, n) {
	fn(f(e) ? e.map((e) => e.bind(t.proxy)) : e.bind(t.proxy), t, n);
}
function Or(e, t, n, r) {
	let i = r.includes(".") ? Bn(n, r) : () => n[r];
	if (_(e)) {
		let n = t[e];
		g(n) && Ln(i, n);
	} else if (g(e)) Ln(i, e.bind(n));
	else if (y(e)) {
		if (f(e)) e.forEach((e) => Or(e, t, n, r));
		else {
			let r = g(e.handler) ? e.handler.bind(n) : t[e.handler];
			g(r) && Ln(i, r, e);
		}
	}
}
function kr(e) {
	let t = e.type, { mixins: n, extends: r } = t, { mixins: i, optionsCache: a, config: { optionMergeStrategies: o } } = e.appContext, s = a.get(t), c;
	return s ? c = s : !i.length && !n && !r ? c = t : (c = {}, i.length && i.forEach((e) => Ar(c, e, o, !0)), Ar(c, t, o)), y(t) && a.set(t, c), c;
}
function Ar(e, t, n, r = !1) {
	let { mixins: i, extends: a } = t;
	a && Ar(e, a, n, !0), i && i.forEach((t) => Ar(e, t, n, !0));
	for (let i in t) if (!(r && i === "expose")) {
		let r = jr[i] || n && n[i];
		e[i] = r ? r(e[i], t[i]) : t[i];
	}
	return e;
}
var jr = {
	data: Mr,
	props: Ir,
	emits: Ir,
	methods: Fr,
	computed: Fr,
	beforeCreate: V,
	created: V,
	beforeMount: V,
	mounted: V,
	beforeUpdate: V,
	updated: V,
	beforeDestroy: V,
	beforeUnmount: V,
	destroyed: V,
	unmounted: V,
	activated: V,
	deactivated: V,
	errorCaptured: V,
	serverPrefetch: V,
	components: Fr,
	directives: Fr,
	watch: Lr,
	provide: Mr,
	inject: Nr
};
function Mr(e, t) {
	return t ? e ? function() {
		return c(g(e) ? e.call(this, this) : e, g(t) ? t.call(this, this) : t);
	} : t : e;
}
function Nr(e, t) {
	return Fr(Pr(e), Pr(t));
}
function Pr(e) {
	if (f(e)) {
		let t = {};
		for (let n = 0; n < e.length; n++) t[e[n]] = e[n];
		return t;
	}
	return e;
}
function V(e, t) {
	return e ? [...new Set([].concat(e, t))] : t;
}
function Fr(e, t) {
	return e ? c(/* @__PURE__ */ Object.create(null), e, t) : t;
}
function Ir(e, t) {
	return e ? f(e) && f(t) ? [.../* @__PURE__ */ new Set([...e, ...t])] : c(/* @__PURE__ */ Object.create(null), Cr(e), Cr(t ?? {})) : t;
}
function Lr(e, t) {
	if (!e) return t;
	if (!t) return e;
	let n = c(/* @__PURE__ */ Object.create(null), e);
	for (let r in t) n[r] = V(e[r], t[r]);
	return n;
}
function Rr() {
	return {
		app: null,
		config: {
			isNativeTag: a,
			performance: !1,
			globalProperties: {},
			optionMergeStrategies: {},
			errorHandler: void 0,
			warnHandler: void 0,
			compilerOptions: {}
		},
		mixins: [],
		components: {},
		directives: {},
		provides: /* @__PURE__ */ Object.create(null),
		optionsCache: /* @__PURE__ */ new WeakMap(),
		propsCache: /* @__PURE__ */ new WeakMap(),
		emitsCache: /* @__PURE__ */ new WeakMap()
	};
}
var zr = 0;
function Br(e, t) {
	return function(n, r = null) {
		g(n) || (n = c({}, n)), r != null && !y(r) && (r = null);
		let i = Rr(), a = /* @__PURE__ */ new WeakSet(), o = [], s = !1, l = i.app = {
			_uid: zr++,
			_component: n,
			_props: r,
			_container: null,
			_context: i,
			_instance: null,
			version: ma,
			get config() {
				return i.config;
			},
			set config(e) {},
			use(e, ...t) {
				return a.has(e) || (e && g(e.install) ? (a.add(e), e.install(l, ...t)) : g(e) && (a.add(e), e(l, ...t))), l;
			},
			mixin(e) {
				return i.mixins.includes(e) || i.mixins.push(e), l;
			},
			component(e, t) {
				return t ? (i.components[e] = t, l) : i.components[e];
			},
			directive(e, t) {
				return t ? (i.directives[e] = t, l) : i.directives[e];
			},
			mount(a, o, c) {
				if (!s) {
					let u = l._ceVNode || Y(n, r);
					return u.appContext = i, c === !0 ? c = "svg" : c === !1 && (c = void 0), o && t ? t(u, a) : e(u, a, c), s = !0, l._container = a, a.__vue_app__ = l, fa(u.component);
				}
			},
			onUnmount(e) {
				o.push(e);
			},
			unmount() {
				s && (fn(o, l._instance, 16), e(null, l._container), delete l._container.__vue_app__);
			},
			provide(e, t) {
				return i.provides[e] = t, l;
			},
			runWithContext(e) {
				let t = Vr;
				Vr = l;
				try {
					return e();
				} finally {
					Vr = t;
				}
			}
		};
		return l;
	};
}
var Vr = null, Hr = (e, t) => t === "modelValue" || t === "model-value" ? e.modelModifiers : e[`${t}Modifiers`] || e[`${T(t)}Modifiers`] || e[`${E(t)}Modifiers`];
function Ur(e, t, ...r) {
	if (e.isUnmounted) return;
	let i = e.vnode.props || n, a = r, o = t.startsWith("update:"), s = o && Hr(i, t.slice(7));
	s && (s.trim && (a = r.map((e) => _(e) ? e.trim() : e)), s.number && (a = a.map(le)));
	let c, l = i[c = oe(t)] || i[c = oe(T(t))];
	!l && o && (l = i[c = oe(E(t))]), l && fn(l, e, 6, a);
	let u = i[c + "Once"];
	if (u) {
		if (!e.emitted) e.emitted = {};
		else if (e.emitted[c]) return;
		e.emitted[c] = !0, fn(u, e, 6, a);
	}
}
var Wr = /* @__PURE__ */ new WeakMap();
function Gr(e, t, n = !1) {
	let r = n ? Wr : t.emitsCache, i = r.get(e);
	if (i !== void 0) return i;
	let a = e.emits, o = {}, s = !1;
	if (!g(e)) {
		let r = (e) => {
			let n = Gr(e, t, !0);
			n && (s = !0, c(o, n));
		};
		!n && t.mixins.length && t.mixins.forEach(r), e.extends && r(e.extends), e.mixins && e.mixins.forEach(r);
	}
	return !a && !s ? (y(e) && r.set(e, null), null) : (f(a) ? a.forEach((e) => o[e] = null) : c(o, a), y(e) && r.set(e, o), o);
}
function Kr(e, t) {
	return !e || !o(t) ? !1 : (t = t.slice(2), t = t === "Once" ? t : t.replace(/Once$/, ""), d(e, t[0].toLowerCase() + t.slice(1)) || d(e, E(t)) || d(e, t));
}
function qr(e) {
	let { type: t, vnode: n, proxy: r, withProxy: i, propsOptions: [a], slots: o, attrs: c, emit: l, render: u, renderCache: d, props: f, data: p, setupState: m, ctx: h, inheritAttrs: g } = e, _ = jn(e), v, y;
	try {
		if (n.shapeFlag & 4) {
			let e = i || r, t = e;
			v = Gi(u.call(t, e, d, f, m, p, h)), y = c;
		} else {
			let e = t;
			v = Gi(e.length > 1 ? e(f, {
				attrs: c,
				slots: o,
				emit: l
			}) : e(f, null)), y = t.props ? c : Jr(c);
		}
	} catch (t) {
		Ni.length = 0, pn(t, e, 1), v = Y(ji);
	}
	let b = v;
	if (y && g !== !1) {
		let e = Object.keys(y), { shapeFlag: t } = b;
		e.length && t & 7 && (a && e.some(s) && (y = Yr(y, a)), b = Wi(b, y, !1, !0));
	}
	return n.dirs && (b = Wi(b, null, !1, !0), b.dirs = b.dirs ? b.dirs.concat(n.dirs) : n.dirs), n.transition && Kn(Hn(b.type) && Gn(b) || b, n.transition), v = b, jn(_), v;
}
var Jr = (e) => {
	let t;
	for (let n in e) (n === "class" || n === "style" || o(n)) && ((t ||= {})[n] = e[n]);
	return t;
}, Yr = (e, t) => {
	let n = {};
	for (let r in e) (!s(r) || !(r.slice(9) in t)) && (n[r] = e[r]);
	return n;
};
function Xr(e, t, n) {
	let { props: r, children: i, component: a } = e, { props: o, children: s, patchFlag: c } = t, l = a.emitsOptions;
	if (t.dirs || t.transition) return !0;
	if (n && c >= 0) {
		if (c & 1024) return !0;
		if (c & 16) return r ? Zr(r, o, l) : !!o;
		if (c & 8) {
			let e = t.dynamicProps;
			for (let t = 0; t < e.length; t++) {
				let n = e[t];
				if (Qr(o, r, n) && !Kr(l, n)) return !0;
			}
		}
	} else return (i || s) && (!s || !s.$stable) ? !0 : r === o ? !1 : r ? !o || Zr(r, o, l) : !!o;
	return !1;
}
function Zr(e, t, n) {
	let r = Object.keys(t);
	if (r.length !== Object.keys(e).length) return !0;
	for (let i = 0; i < r.length; i++) {
		let a = r[i];
		if (Qr(t, e, a) && !Kr(n, a)) return !0;
	}
	return !1;
}
function Qr(e, t, n) {
	let r = e[n], i = t[n];
	return n === "style" && y(r) && y(i) ? !Ee(r, i) : r !== i;
}
function $r({ vnode: e, parent: t, suspense: n }, r) {
	for (; t;) {
		let n = t.subTree;
		if (n.suspense && n.suspense.activeBranch === e && (n.suspense.vnode.el = n.el = r, e = n), n === e) (e = t.vnode).el = r, t = t.parent;
		else break;
	}
	n && n.activeBranch === e && (n.vnode.el = r);
}
var ei = {}, ti = () => Object.create(ei), ni = (e) => Object.getPrototypeOf(e) === ei;
function ri(e, t, n, r = !1) {
	let i = {}, a = ti();
	e.propsDefaults = /* @__PURE__ */ Object.create(null), ai(e, t, i, a);
	for (let t in e.propsOptions[0]) t in i || (i[t] = void 0);
	e.props = n ? r ? i : /* @__PURE__ */ Vt(i) : e.type.props ? i : a, e.attrs = a;
}
function ii(e, t, n, r) {
	let { props: i, attrs: a, vnode: { patchFlag: o } } = e, s = /* @__PURE__ */ M(i), [c] = e.propsOptions, l = !1;
	if ((r || o > 0) && !(o & 16)) {
		if (o & 8) {
			let n = e.vnode.dynamicProps;
			for (let r = 0; r < n.length; r++) {
				let o = n[r];
				if (Kr(e.emitsOptions, o)) continue;
				let u = t[o];
				if (c) {
					if (d(a, o)) u !== a[o] && (a[o] = u, l = !0);
					else {
						let t = T(o);
						i[t] = oi(c, s, t, u, e, !1);
					}
				} else u !== a[o] && (a[o] = u, l = !0);
			}
		}
	} else {
		ai(e, t, i, a) && (l = !0);
		let r;
		for (let a in s) (!t || !d(t, a) && ((r = E(a)) === a || !d(t, r))) && (c ? n && (n[a] !== void 0 || n[r] !== void 0) && (i[a] = oi(c, s, a, void 0, e, !0)) : delete i[a]);
		if (a !== s) for (let e in a) (!t || !d(t, e)) && (delete a[e], l = !0);
	}
	l && ot(e.attrs, "set", "");
}
function ai(e, t, r, i) {
	let [a, o] = e.propsOptions, s = !1, c;
	if (t) for (let n in t) {
		if (te(n)) continue;
		let l = t[n], u;
		a && d(a, u = T(n)) ? !o || !o.includes(u) ? r[u] = l : (c ||= {})[u] = l : Kr(e.emitsOptions, n) || (!(n in i) || l !== i[n]) && (i[n] = l, s = !0);
	}
	if (o) {
		let t = /* @__PURE__ */ M(r), i = c || n;
		for (let n = 0; n < o.length; n++) {
			let s = o[n];
			r[s] = oi(a, t, s, i[s], e, !d(i, s));
		}
	}
	return s;
}
function oi(e, t, n, r, i, a) {
	let o = e[n];
	if (o != null) {
		let e = d(o, "default");
		if (e && r === void 0) {
			let e = o.default;
			if (o.type !== Function && !o.skipFactory && g(e)) {
				let { propsDefaults: a } = i;
				if (n in a) r = a[n];
				else {
					let o = na(i);
					r = a[n] = e.call(null, t), o();
				}
			} else r = e;
			i.ce && i.ce._setProp(n, r);
		}
		o[0] && (a && !e ? r = !1 : o[1] && (r === "" || r === E(n)) && (r = !0));
	}
	return r;
}
var si = /* @__PURE__ */ new WeakMap();
function ci(e, t, i = !1) {
	let a = i ? si : t.propsCache, o = a.get(e);
	if (o) return o;
	let s = e.props, l = {}, u = [], p = !1;
	if (!g(e)) {
		let n = (e) => {
			p = !0;
			let [n, r] = ci(e, t, !0);
			c(l, n), r && u.push(...r);
		};
		!i && t.mixins.length && t.mixins.forEach(n), e.extends && n(e.extends), e.mixins && e.mixins.forEach(n);
	}
	if (!s && !p) return y(e) && a.set(e, r), r;
	if (f(s)) for (let e = 0; e < s.length; e++) {
		let t = T(s[e]);
		li(t) && (l[t] = n);
	}
	else if (s) for (let e in s) {
		let t = T(e);
		if (li(t)) {
			let n = s[e], r = l[t] = f(n) || g(n) ? { type: n } : c({}, n), i = r.type, a = !1, o = !0;
			if (f(i)) for (let e = 0; e < i.length; ++e) {
				let t = i[e], n = g(t) && t.name;
				if (n === "Boolean") {
					a = !0;
					break;
				}
				n === "String" && (o = !1);
			}
			else a = g(i) && i.name === "Boolean";
			r[0] = a, r[1] = o, (a || d(r, "default")) && u.push(t);
		}
	}
	let m = [l, u];
	return y(e) && a.set(e, m), m;
}
function li(e) {
	return e[0] !== "$" && !te(e);
}
var ui = (e) => e === "_" || e === "_ctx" || e === "$stable", di = (e) => f(e) ? e.map(Gi) : [Gi(e)], fi = (e, t, n) => {
	if (t._n) return t;
	let r = R((...e) => di(t(...e)), n);
	return r._c = !1, r;
}, pi = (e, t, n) => {
	let r = e._ctx;
	for (let n in e) {
		if (ui(n)) continue;
		let i = e[n];
		if (g(i)) t[n] = fi(n, i, r);
		else if (i != null) {
			let e = di(i);
			t[n] = () => e;
		}
	}
}, mi = (e, t) => {
	let n = di(t);
	e.slots.default = () => n;
}, hi = (e, t, n) => {
	for (let r in t) (n || !ui(r)) && (e[r] = t[r]);
}, gi = (e, t, n) => {
	let r = e.slots = ti();
	if (e.vnode.shapeFlag & 32) {
		let e = t._;
		e ? (hi(r, t, n), n && ce(r, "_", e, !0)) : pi(t, r);
	} else t && mi(e, t);
}, _i = (e, t, r) => {
	let { vnode: i, slots: a } = e, o = !0, s = n;
	if (i.shapeFlag & 32) {
		let e = t._;
		e ? r && e === 1 ? o = !1 : hi(a, t, r) : (o = !t.$stable, pi(t, a)), s = t;
	} else t && (mi(e, t), s = { default: 1 });
	if (o) for (let e in a) !ui(e) && s[e] == null && delete a[e];
}, H = ki;
function vi(e) {
	return yi(e);
}
function yi(e, t) {
	let a = fe();
	a.__VUE__ = !0;
	let { insert: o, remove: s, patchProp: c, createElement: l, createText: u, createComment: d, setText: f, setElementText: p, parentNode: m, nextSibling: h, setScopeId: g = i, insertStaticContent: _ } = e, v = (e, t, n, i = null, a = null, o = null, s = void 0, c = null, l = !!t.dynamicChildren) => {
		if (e === t) return;
		e && !zi(e, t) && (i = xe(e), ge(e, a, o, !0), e = null), t.patchFlag === -2 && (l = !1, t.dynamicChildren = null), t.dynamicChildren && e && e.dynamicChildren && e.dynamicChildren.hasOnce && (t.dynamicChildren === r && (t.dynamicChildren = []), t.dynamicChildren.hasOnce = !0);
		let { type: u, ref: d, shapeFlag: f } = t;
		switch (u) {
			case Ai:
				y(e, t, n, i);
				break;
			case ji:
				b(e, t, n, i);
				break;
			case Mi:
				e ?? x(t, n, i, s);
				break;
			case U:
				ae(e, t, n, i, a, o, s, c, l);
				break;
			default: f & 1 ? w(e, t, n, i, a, o, s, c, l) : f & 6 ? oe(e, t, n, i, a, o, s, c, l) : (f & 64 || f & 128) && u.process(e, t, n, i, a, o, s, c, l, we);
		}
		d != null && a ? Xn(d, e && e.ref, o, t || e, !t) : d == null && e && e.ref != null && Xn(e.ref, null, o, e, !0);
	}, y = (e, t, n, r) => {
		if (e == null) o(t.el = u(t.children), n, r);
		else {
			let n = t.el = e.el;
			t.children !== e.children && f(n, t.children);
		}
	}, b = (e, t, n, r) => {
		e == null ? o(t.el = d(t.children || ""), n, r) : t.el = e.el;
	}, x = (e, t, n, r) => {
		[e.el, e.anchor] = _(e.children, t, n, r, e.el, e.anchor);
	}, S = ({ el: e, anchor: t }, n, r) => {
		let i;
		for (; e && e !== t;) i = h(e), o(e, n, r), e = i;
		o(t, n, r);
	}, C = ({ el: e, anchor: t }) => {
		let n;
		for (; e && e !== t;) n = h(e), s(e), e = n;
		s(t);
	}, w = (e, t, n, r, i, a, o, s, c) => {
		if (t.type === "svg" ? o = "svg" : t.type === "math" && (o = "mathml"), e == null) ee(t, n, r, i, a, o, s, c);
		else {
			let n = e.el && e.el._isVueCE ? e.el : null;
			try {
				n && n._beginPatch(), T(e, t, i, a, o, s, c);
			} finally {
				n && n._endPatch();
			}
		}
	}, ee = (e, t, n, r, i, a, s, u) => {
		let d, f, { props: m, shapeFlag: h, transition: g, dirs: _ } = e;
		if (d = e.el = l(e.type, a, m && m.is, m), h & 8 ? p(d, e.children) : h & 16 && re(e.children, d, null, r, i, bi(e, a), s, u), _ && Mn(e, null, r, "created"), ne(d, e, e.scopeId, s, r), m) {
			for (let e in m) e !== "value" && !te(e) && c(d, e, null, m[e], a, r);
			"value" in m && c(d, "value", null, m.value, a), (f = m.onVnodeBeforeMount) && Yi(f, r, e);
		}
		_ && Mn(e, null, r, "beforeMount");
		let v = Si(i, g);
		v && g.beforeEnter(d), o(d, t, n), ((f = m && m.onVnodeMounted) || v || _) && H(() => {
			try {
				f && Yi(f, r, e), v && g.enter(d), _ && Mn(e, null, r, "mounted");
			} finally {}
		}, i);
	}, ne = (e, t, n, r, i) => {
		if (n && g(e, n), r) for (let t = 0; t < r.length; t++) g(e, r[t]);
		if (i) {
			let n = i.subTree;
			if (t === n || Oi(n.type) && (n.ssContent === t || n.ssFallback === t)) {
				let t = i.vnode;
				ne(e, t, t.scopeId, t.slotScopeIds, i.parent);
			}
		}
	}, re = (e, t, n, r, i, a, o, s, c = 0) => {
		for (let l = c; l < e.length; l++) {
			let c = e[l] = s ? Ki(e[l]) : Gi(e[l]);
			v(null, c, t, n, r, i, a, o, s);
		}
	}, T = (e, t, r, i, a, o, s) => {
		let l = t.el = e.el, { patchFlag: u, dynamicChildren: d, dirs: f } = t;
		u |= e.patchFlag & 16;
		let m = e.props || n, h = t.props || n, g;
		if (r && xi(r, !1), (g = h.onVnodeBeforeUpdate) && Yi(g, r, t, e), f && Mn(t, e, r, "beforeUpdate"), r && xi(r, !0), d && (!e.dynamicChildren || e.dynamicChildren.length !== d.length) && (u = 0, s = !1, d = null), (m.innerHTML && h.innerHTML == null || m.textContent && h.textContent == null) && p(l, ""), d ? ie(e.dynamicChildren, d, l, r, i, bi(t, a), o) : s || de(e, t, l, null, r, i, bi(t, a), o, !1), u > 0) {
			if (u & 16) E(l, m, h, r, a);
			else if (u & 2 && m.class !== h.class && c(l, "class", null, h.class, a), u & 4 && c(l, "style", m.style, h.style, a), u & 8) {
				let e = t.dynamicProps;
				for (let t = 0; t < e.length; t++) {
					let n = e[t], i = m[n], o = h[n];
					(o !== i || n === "value") && c(l, n, i, o, a, r);
				}
			}
			u & 1 && e.children !== t.children && p(l, t.children);
		} else !s && d == null && E(l, m, h, r, a);
		((g = h.onVnodeUpdated) || f) && H(() => {
			g && Yi(g, r, t, e), f && Mn(t, e, r, "updated");
		}, i);
	}, ie = (e, t, n, r, i, a, o) => {
		for (let s = 0; s < t.length; s++) {
			let c = e[s], l = t[s], u = c.el && (c.type === U || !zi(c, l) || c.shapeFlag & 198) ? m(c.el) : n;
			v(c, l, u, null, r, i, a, o, !0);
		}
	}, E = (e, t, r, i, a) => {
		if (t !== r) {
			if (t !== n) for (let n in t) !te(n) && !(n in r) && c(e, n, t[n], null, a, i);
			for (let n in r) {
				if (te(n)) continue;
				let o = r[n], s = t[n];
				o !== s && n !== "value" && c(e, n, s, o, a, i);
			}
			"value" in r && c(e, "value", t.value, r.value, a);
		}
	}, ae = (e, t, n, r, i, a, s, c, l) => {
		let d = t.el = e ? e.el : u(""), f = t.anchor = e ? e.anchor : u(""), { patchFlag: p, dynamicChildren: m, slotScopeIds: h } = t;
		h && (c = c ? c.concat(h) : h), e == null ? (o(d, n, r), o(f, n, r), re(t.children || [], n, f, i, a, s, c, l)) : p > 0 && p & 64 && m && e.dynamicChildren && e.dynamicChildren.length === m.length ? (ie(e.dynamicChildren, m, n, i, a, s, c), (t.key != null || i && t === i.subTree) && Ci(e, t, !0)) : de(e, t, n, f, i, a, s, c, l);
	}, oe = (e, t, n, r, i, a, o, s, c) => {
		t.slotScopeIds = s, e == null ? t.shapeFlag & 512 ? i.ctx.activate(t, n, r, o, c) : se(t, n, r, i, a, o, c) : ce(e, t, c);
	}, se = (e, t, n, r, i, a, o) => {
		let s = e.component = Qi(e, r, i);
		if ($n(e) && (s.ctx.renderer = we), oa(s, !1, o), s.asyncDep) {
			if (i && i.registerDep(s, le, o), !e.el) {
				let r = s.subTree = Y(ji);
				b(null, r, t, n), e.placeholder = r.el;
			}
		} else le(s, e, t, n, i, a, o);
	}, ce = (e, t, n) => {
		let r = t.component = e.component;
		if (Xr(e, t, n)) {
			if (r.asyncDep && !r.asyncResolved) {
				t.el = e.el, ue(r, t, n);
				return;
			}
			r.next = t, r.update();
		} else t.el = e.el, r.vnode = t;
	}, le = (e, t, n, r, i, a, o) => {
		let s = () => {
			if (e.isMounted) {
				let { next: t, bu: n, u: r, parent: s, vnode: c } = e;
				{
					let n = Ti(e);
					if (n) {
						t && (t.el = c.el, ue(e, t, o)), n.asyncDep.then(() => {
							H(() => {
								e.isUnmounted || l();
							}, i);
						});
						return;
					}
				}
				let u = t, d;
				xi(e, !1), t ? (t.el = c.el, ue(e, t, o)) : t = c, n && D(n), (d = t.props && t.props.onVnodeBeforeUpdate) && Yi(d, s, t, c), xi(e, !0);
				let f = qr(e), p = e.subTree;
				e.subTree = f, v(p, f, m(p.el), xe(p), e, i, a), t.el = f.el, u === null && $r(e, f.el), r && H(r, i), (d = t.props && t.props.onVnodeUpdated) && H(() => Yi(d, s, t, c), i);
			} else {
				let o, { el: s, props: c } = t, { bm: l, m: u, parent: d, root: f, type: p } = e, m = Qn(t);
				if (xi(e, !1), l && D(l), !m && (o = c && c.onVnodeBeforeMount) && Yi(o, d, t), xi(e, !0), s && Ee) {
					let t = () => {
						e.subTree = qr(e), Ee(s, e.subTree, e, i, null);
					};
					m && p.__asyncHydrate ? p.__asyncHydrate(s, e, t) : t();
				} else {
					f.ce && f.ce._hasShadowRoot() && f.ce._injectChildStyle(p, e.parent ? e.parent.type : void 0);
					let o = e.subTree = qr(e);
					v(null, o, n, r, e, i, a), t.el = o.el;
				}
				if (u && H(u, i), !m && (o = c && c.onVnodeMounted)) {
					let e = t;
					H(() => Yi(o, d, e), i);
				}
				(t.shapeFlag & 256 || d && Qn(d.vnode) && d.vnode.shapeFlag & 256) && e.a && H(e.a, i), e.isMounted = !0, t = n = r = null;
			}
		};
		e.scope.on();
		let c = e.effect = new Pe(s);
		e.scope.off();
		let l = e.update = c.run.bind(c), u = e.job = c.runIfDirty.bind(c);
		u.i = e, u.id = e.uid, c.scheduler = () => Cn(u), xi(e, !0), l();
	}, ue = (e, t, n) => {
		t.component = e;
		let r = e.vnode.props;
		e.vnode = t, e.next = null, ii(e, t.props, r, n), _i(e, t.children, n), Ye(), En(e), Xe();
	}, de = (e, t, n, r, i, a, o, s, c = !1) => {
		let l = e && e.children, u = e ? e.shapeFlag : 0, d = t.children, { patchFlag: f, shapeFlag: m } = t;
		if (f > 0) {
			if (f & 128) {
				me(l, d, n, r, i, a, o, s, c);
				return;
			}
			if (f & 256) {
				pe(l, d, n, r, i, a, o, s, c);
				return;
			}
		}
		m & 8 ? (u & 16 && be(l, i, a), d !== l && p(n, d)) : u & 16 ? m & 16 ? me(l, d, n, r, i, a, o, s, c) : be(l, i, a, !0) : (u & 8 && p(n, ""), m & 16 && re(d, n, r, i, a, o, s, c));
	}, pe = (e, t, n, i, a, o, s, c, l) => {
		e ||= r, t ||= r;
		let u = e.length, d = t.length, f = Math.min(u, d), p = 0;
		for (; p < f; p++) {
			let r = t[p] = l ? Ki(t[p]) : Gi(t[p]);
			v(e[p], r, n, null, a, o, s, c, l);
		}
		u > d ? be(e, a, o, !0, !1, f) : re(t, n, i, a, o, s, c, l, f);
	}, me = (e, t, n, i, a, o, s, c, l) => {
		let u = 0, d = t.length, f = e.length - 1, p = d - 1;
		for (; u <= f && u <= p;) {
			let r = e[u], i = t[u] = l ? Ki(t[u]) : Gi(t[u]);
			if (zi(r, i)) v(r, i, n, null, a, o, s, c, l);
			else break;
			u++;
		}
		for (; u <= f && u <= p;) {
			let r = e[f], i = t[p] = l ? Ki(t[p]) : Gi(t[p]);
			if (zi(r, i)) v(r, i, n, null, a, o, s, c, l);
			else break;
			f--, p--;
		}
		if (u > f) {
			if (u <= p) {
				let e = p + 1, r = e < d ? t[e].el : i;
				for (; u <= p;) v(null, t[u] = l ? Ki(t[u]) : Gi(t[u]), n, r, a, o, s, c, l), u++;
			}
		} else if (u > p) for (; u <= f;) ge(e[u], a, o, !0), u++;
		else {
			let m = u, h = u, g = /* @__PURE__ */ new Map();
			for (u = h; u <= p; u++) {
				let e = t[u] = l ? Ki(t[u]) : Gi(t[u]);
				e.key != null && g.set(e.key, u);
			}
			let _, y = 0, b = p - h + 1, x = !1, S = 0, C = Array(b);
			for (u = 0; u < b; u++) C[u] = 0;
			for (u = m; u <= f; u++) {
				let r = e[u];
				if (y >= b) {
					ge(r, a, o, !0);
					continue;
				}
				let i;
				if (r.key != null) i = g.get(r.key);
				else for (_ = h; _ <= p; _++) if (C[_ - h] === 0 && zi(r, t[_])) {
					i = _;
					break;
				}
				i === void 0 ? ge(r, a, o, !0) : (C[i - h] = u + 1, i >= S ? S = i : x = !0, v(r, t[i], n, null, a, o, s, c, l), y++);
			}
			let w = x ? wi(C) : r;
			for (_ = w.length - 1, u = b - 1; u >= 0; u--) {
				let e = h + u, r = t[e], f = t[e + 1], p = e + 1 < d ? f.el || Di(f) : i;
				C[u] === 0 ? v(null, r, n, p, a, o, s, c, l) : x && (_ < 0 || u !== w[_] ? he(r, n, p, 2) : _--);
			}
		}
	}, he = (e, t, n, r, i = null) => {
		let { el: a, type: c, transition: l, children: u, shapeFlag: d } = e;
		if (d & 6) {
			he(e.component.subTree, t, n, r);
			return;
		}
		if (d & 128) {
			e.suspense.move(t, n, r);
			return;
		}
		if (d & 64) {
			c.move(e, t, n, we);
			return;
		}
		if (c === U) {
			o(a, t, n);
			for (let e = 0; e < u.length; e++) he(u[e], t, n, r);
			o(e.anchor, t, n);
			return;
		}
		if (c === Mi) {
			S(e, t, n);
			return;
		}
		if (r !== 2 && d & 1 && l) {
			if (r === 0) l.persisted && !a[Un] ? o(a, t, n) : (l.beforeEnter(a), o(a, t, n), H(() => l.enter(a), i));
			else {
				let { leave: r, delayLeave: i, afterLeave: c } = l, u = () => {
					e.ctx.isUnmounted ? s(a) : o(a, t, n);
				}, d = () => {
					let e = a._isLeaving || !!a[Un];
					a._isLeaving && a[Un](!0), l.persisted && !e ? u() : r(a, () => {
						u(), c && c();
					});
				};
				i ? i(a, u, d) : d();
			}
		} else o(a, t, n);
	}, ge = (e, t, n, r = !1, i = !1) => {
		let { type: a, props: o, ref: s, children: c, dynamicChildren: l, shapeFlag: u, patchFlag: d, dirs: f, cacheIndex: p, memo: m } = e;
		if ((d === -2 || l && l.hasOnce) && (i = !1), s != null && (Ye(), Xn(s, null, n, e, !0), Xe()), p != null && (!e.ctx || e.ctx === t) && (t.renderCache[p] = void 0), u & 256) {
			t.ctx.deactivate(e);
			return;
		}
		let h = u & 1 && f, g = !Qn(e), _;
		if (g && (_ = o && o.onVnodeBeforeUnmount) && Yi(_, t, e), u & 6) ye(e.component, n, r);
		else {
			if (u & 128) {
				e.suspense.unmount(n, r);
				return;
			}
			h && Mn(e, null, t, "beforeUnmount"), u & 64 ? e.type.remove(e, t, n, we, r) : l && !l.hasOnce && (a !== U || d > 0 && d & 64) ? be(l, t, n, !1, !0) : (a === U && d & 384 || !i && u & 16) && be(c, t, n), r && _e(e);
		}
		let v = m != null && p == null;
		(g && (_ = o && o.onVnodeUnmounted) || h || v) && H(() => {
			_ && Yi(_, t, e), h && Mn(e, null, t, "unmounted"), v && (e.el = null);
		}, n);
	}, _e = (e) => {
		let { type: t, el: n, anchor: r, transition: i } = e;
		if (t === U) {
			ve(n, r);
			return;
		}
		if (t === Mi) {
			C(e), i && !i.persisted && i.afterLeave && i.afterLeave();
			return;
		}
		let a = () => {
			s(n), i && !i.persisted && i.afterLeave && i.afterLeave();
		};
		if (e.shapeFlag & 1 && i && !i.persisted) {
			let { leave: t, delayLeave: r } = i, o = () => t(n, a);
			r ? r(e.el, a, o) : o();
		} else a();
	}, ve = (e, t) => {
		let n;
		for (; e !== t;) n = h(e), s(e), e = n;
		s(t);
	}, ye = (e, t, n) => {
		let { bum: r, scope: i, job: a, subTree: o, um: s, m: c, a: l } = e;
		Ei(c), Ei(l), r && D(r), i.stop(), a ? (a.flags |= 8, ge(o, e, t, n)) : e.vnode.el && o && (o.transition = e.vnode.transition, ge(o, e, t, n)), s && H(s, t), H(() => {
			e.isUnmounted = !0;
		}, t);
	}, be = (e, t, n, r = !1, i = !1, a = 0) => {
		for (let o = a; o < e.length; o++) ge(e[o], t, n, r, i);
	}, xe = (e) => {
		if (e.shapeFlag & 6) return xe(e.component.subTree);
		if (e.shapeFlag & 128) return e.suspense.next();
		let t = h(e.anchor || e.el), n = t && t[Vn];
		return n ? h(n) : t;
	}, Se = !1, Ce = (e, t, n) => {
		let r;
		e == null ? t._vnode && (ge(t._vnode, null, null, !0), r = t._vnode.component) : v(t._vnode || null, e, t, null, null, null, n), t._vnode = e, Se ||= (Se = !0, En(r), Dn(), !1);
	}, we = {
		p: v,
		um: ge,
		m: he,
		r: _e,
		mt: se,
		mc: re,
		pc: de,
		pbc: ie,
		n: xe,
		o: e
	}, Te, Ee;
	return t && ([Te, Ee] = t(we)), {
		render: Ce,
		hydrate: Te,
		createApp: Br(Ce, Te)
	};
}
function bi({ type: e, props: t }, n) {
	return n === "svg" && e === "foreignObject" || n === "mathml" && e === "annotation-xml" && t && t.encoding && t.encoding.includes("html") ? void 0 : n;
}
function xi({ effect: e, job: t }, n) {
	n ? (e.flags |= 32, t.flags |= 4) : (e.flags &= -33, t.flags &= -5);
}
function Si(e, t) {
	return (!e || e && !e.pendingBranch) && t && !t.persisted;
}
function Ci(e, t, n = !1) {
	let r = e.children, i = t.children;
	if (f(r) && f(i)) for (let e = 0; e < r.length; e++) {
		let t = r[e], a = i[e];
		a.shapeFlag & 1 && !a.dynamicChildren && ((a.patchFlag <= 0 || a.patchFlag === 32) && (a = i[e] = Ki(i[e]), a.el = t.el), !n && a.patchFlag !== -2 && Ci(t, a)), a.type === Ai && (a.patchFlag === -1 && (a = i[e] = Ki(a)), a.el = t.el), a.type === ji && !a.el && (a.el = t.el);
	}
}
function wi(e) {
	let t = e.slice(), n = [0], r, i, a, o, s, c = e.length;
	for (r = 0; r < c; r++) {
		let c = e[r];
		if (c !== 0) {
			if (i = n[n.length - 1], e[i] < c) {
				t[r] = i, n.push(r);
				continue;
			}
			for (a = 0, o = n.length - 1; a < o;) s = a + o >> 1, e[n[s]] < c ? a = s + 1 : o = s;
			c < e[n[a]] && (a > 0 && (t[r] = n[a - 1]), n[a] = r);
		}
	}
	for (a = n.length, o = n[a - 1]; a-- > 0;) n[a] = o, o = t[o];
	return n;
}
function Ti(e) {
	let t = e.subTree.component;
	if (t) return t.asyncDep && !t.asyncResolved ? t : Ti(t);
}
function Ei(e) {
	if (e) for (let t = 0; t < e.length; t++) e[t].flags |= 8;
}
function Di(e) {
	if (e.placeholder) return e.placeholder;
	let t = e.component;
	return t ? Di(t.subTree) : null;
}
var Oi = (e) => e.__isSuspense;
function ki(e, t) {
	t && t.pendingBranch ? f(e) ? t.effects.push(...e) : t.effects.push(e) : Tn(e);
}
var U = /* @__PURE__ */ Symbol.for("v-fgt"), Ai = /* @__PURE__ */ Symbol.for("v-txt"), ji = /* @__PURE__ */ Symbol.for("v-cmt"), Mi = /* @__PURE__ */ Symbol.for("v-stc"), Ni = [], W = null;
function G(e = !1) {
	Ni.push(W = e ? null : []);
}
function Pi() {
	Ni.pop(), W = Ni[Ni.length - 1] || null;
}
var Fi = 1;
function Ii(e, t = !1) {
	Fi += e, e < 0 && W && t && (W.hasOnce = !0);
}
function Li(e) {
	return e.dynamicChildren = Fi > 0 ? W || r : null, Pi(), Fi > 0 && W && W.push(e), e;
}
function K(e, t, n, r, i, a) {
	return Li(J(e, t, n, r, i, a, !0));
}
function q(e, t, n, r, i) {
	return Li(Y(e, t, n, r, i, !0));
}
function Ri(e) {
	return e ? e.__v_isVNode === !0 : !1;
}
function zi(e, t) {
	return e.type === t.type && e.key === t.key;
}
var Bi = ({ key: e }) => e ?? null, Vi = ({ ref: e, ref_key: t, ref_for: n }) => (typeof e == "number" && (e = "" + e), e == null ? null : _(e) || /* @__PURE__ */ P(e) || g(e) ? {
	i: L,
	r: e,
	k: t,
	f: !!n
} : e);
function J(e, t = null, n = null, r = 0, i = null, a = e === U ? 0 : 1, o = !1, s = !1) {
	let c = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e,
		props: t,
		key: t && Bi(t),
		ref: t && Vi(t),
		scopeId: An,
		slotScopeIds: null,
		children: n,
		component: null,
		suspense: null,
		ssContent: null,
		ssFallback: null,
		dirs: null,
		transition: null,
		el: null,
		anchor: null,
		target: null,
		targetStart: null,
		targetAnchor: null,
		staticCount: 0,
		shapeFlag: a,
		patchFlag: r,
		dynamicProps: i,
		dynamicChildren: null,
		appContext: null,
		ctx: L
	};
	return s ? (qi(c, n), a & 128 && e.normalize(c)) : n && (c.shapeFlag |= _(n) ? 8 : 16), Fi > 0 && !o && W && (c.patchFlag > 0 || a & 6) && c.patchFlag !== 32 && W.push(c), c;
}
var Y = Hi;
function Hi(e, t = null, n = null, r = 0, i = null, a = !1) {
	if ((!e || e === gr) && (e = ji), Ri(e)) {
		let r = Wi(e, t, !0);
		return n && qi(r, n), Fi > 0 && !a && W && (r.shapeFlag & 6 ? W[W.indexOf(e)] = r : W.push(r)), r.patchFlag = -2, r;
	}
	if (pa(e) && (e = e.__vccOpts), t) {
		t = Ui(t);
		let { class: e, style: n } = t;
		e && !_(e) && (t.class = ve(e)), y(n) && (/* @__PURE__ */ qt(n) && !f(n) && (n = c({}, n)), t.style = pe(n));
	}
	let o = _(e) ? 1 : Oi(e) ? 128 : Hn(e) ? 64 : y(e) ? 4 : g(e) ? 2 : 0;
	return J(e, t, n, r, i, o, a, !0);
}
function Ui(e) {
	return e ? /* @__PURE__ */ qt(e) || ni(e) ? c({}, e) : e : null;
}
function Wi(e, t, n = !1, r = !1) {
	let { props: i, ref: a, patchFlag: o, children: s, transition: c } = e, l = t ? Ji(i || {}, t) : i, u = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e.type,
		props: l,
		key: l && Bi(l),
		ref: t && t.ref ? n && a ? f(a) ? a.concat(Vi(t)) : [a, Vi(t)] : Vi(t) : a,
		scopeId: e.scopeId,
		slotScopeIds: e.slotScopeIds,
		children: s,
		target: e.target,
		targetStart: e.targetStart,
		targetAnchor: e.targetAnchor,
		staticCount: e.staticCount,
		shapeFlag: e.shapeFlag,
		patchFlag: t && e.type !== U ? o === -1 ? 16 : o | 16 : o,
		dynamicProps: e.dynamicProps,
		dynamicChildren: e.dynamicChildren,
		appContext: e.appContext,
		dirs: e.dirs,
		transition: c,
		component: e.component,
		suspense: e.suspense,
		ssContent: e.ssContent && Wi(e.ssContent),
		ssFallback: e.ssFallback && Wi(e.ssFallback),
		placeholder: e.placeholder,
		el: e.el,
		anchor: e.anchor,
		ctx: e.ctx,
		ce: e.ce,
		cacheIndex: e.cacheIndex
	};
	return c && r && Kn(u, c.clone(u)), u;
}
function X(e = " ", t = 0) {
	return Y(Ai, null, e, t);
}
function Z(e = "", t = !1) {
	return t ? (G(), q(ji, null, e)) : Y(ji, null, e);
}
function Gi(e) {
	return e == null || typeof e == "boolean" ? Y(ji) : f(e) ? Y(U, null, e.slice()) : Ri(e) ? Ki(e) : Y(Ai, null, String(e));
}
function Ki(e) {
	return e.el === null && e.patchFlag !== -1 || e.memo ? e : Wi(e);
}
function qi(e, t) {
	let n = 0, { shapeFlag: r } = e;
	if (t == null) t = null;
	else if (f(t)) n = 16;
	else if (typeof t == "object") {
		if (r & 65) {
			let n = t.default;
			n && (n._c && (n._d = !1), qi(e, n()), n._c && (n._d = !0));
			return;
		}
		{
			n = 32;
			let r = t._;
			!r && !ni(t) ? t._ctx = L : r === 3 && L && (L.slots._ === 1 ? t._ = 1 : (t._ = 2, e.patchFlag |= 1024));
		}
	} else if (g(t)) {
		if (r & 65) {
			qi(e, { default: t });
			return;
		}
		t = {
			default: t,
			_ctx: L
		}, n = 32;
	} else t = String(t), r & 64 ? (n = 16, t = [X(t)]) : n = 8;
	e.children = t, e.shapeFlag |= n;
}
function Ji(...e) {
	let t = {};
	for (let n = 0; n < e.length; n++) {
		let r = e[n];
		for (let e in r) if (e === "class") t.class !== r.class && (t.class = ve([t.class, r.class]));
		else if (e === "style") t.style = pe([t.style, r.style]);
		else if (o(e)) {
			let n = t[e], i = r[e];
			i && n !== i && !(f(n) && n.includes(i)) ? t[e] = n ? [].concat(n, i) : i : i == null && n == null && !s(e) && (t[e] = i);
		} else e !== "" && (t[e] = r[e]);
	}
	return t;
}
function Yi(e, t, n, r = null) {
	fn(e, t, 7, [n, r]);
}
var Xi = Rr(), Zi = 0;
function Qi(e, t, r) {
	let i = e.type, a = (t ? t.appContext : e.appContext) || Xi, o = {
		uid: Zi++,
		vnode: e,
		type: i,
		parent: t,
		appContext: a,
		root: null,
		next: null,
		subTree: null,
		effect: null,
		update: null,
		job: null,
		scope: new Ae(!0),
		render: null,
		proxy: null,
		exposed: null,
		exposeProxy: null,
		withProxy: null,
		provides: t ? t.provides : Object.create(a.provides),
		ids: t ? t.ids : [
			"",
			0,
			0
		],
		accessCache: null,
		renderCache: [],
		components: null,
		directives: null,
		propsOptions: ci(i, a),
		emitsOptions: Gr(i, a),
		emit: null,
		emitted: null,
		propsDefaults: n,
		inheritAttrs: i.inheritAttrs,
		ctx: n,
		data: n,
		props: n,
		attrs: n,
		slots: n,
		refs: n,
		setupState: n,
		setupContext: null,
		suspense: r,
		suspenseId: r ? r.pendingId : 0,
		asyncDep: null,
		asyncResolved: !1,
		isMounted: !1,
		isUnmounted: !1,
		isDeactivated: !1,
		bc: null,
		c: null,
		bm: null,
		m: null,
		bu: null,
		u: null,
		um: null,
		bum: null,
		da: null,
		a: null,
		rtg: null,
		rtc: null,
		ec: null,
		sp: null
	};
	return o.ctx = { _: o }, o.root = t ? t.root : o, o.emit = Ur.bind(null, o), e.ce && e.ce(o), o;
}
var Q = null, $i = () => Q || L, ea, ta;
{
	let e = fe(), t = (t, n) => {
		let r;
		return (r = e[t]) || (r = e[t] = []), r.push(n), (e) => {
			r.length > 1 ? r.forEach((t) => t(e)) : r[0](e);
		};
	};
	ea = t("__VUE_INSTANCE_SETTERS__", (e) => Q = e), ta = t("__VUE_SSR_SETTERS__", (e) => aa = e);
}
var na = (e) => {
	let t = Q;
	return ea(e), e.scope.on(), () => {
		e.scope.off(), ea(t);
	};
}, ra = () => {
	Q && Q.scope.off(), ea(null);
};
function ia(e) {
	return e.vnode.shapeFlag & 4;
}
var aa = !1;
function oa(e, t = !1, n = !1) {
	t && ta(t);
	let { props: r, children: i } = e.vnode, a = ia(e);
	ri(e, r, a, t), gi(e, i, n || t);
	let o = a ? sa(e, t) : void 0;
	return t && ta(!1), o;
}
function sa(e, t) {
	let n = e.type;
	e.accessCache = /* @__PURE__ */ Object.create(null), e.proxy = new Proxy(e.ctx, Sr);
	let { setup: r } = n;
	if (r) {
		Ye();
		let n = e.setupContext = r.length > 1 ? da(e) : null, i = na(e), a = dn(r, e, 0, [e.props, n]), o = b(a);
		if (Xe(), i(), (o || e.sp) && !Qn(e) && qn(e), o) {
			if (a.then(ra, ra), t) return a.then((n) => {
				ta(!0);
				try {
					ca(e, n, t);
				} finally {
					ta(!1);
				}
			}).catch((t) => {
				pn(t, e, 0);
			});
			e.asyncDep = a;
		} else ca(e, a, t);
	} else la(e, t);
}
function ca(e, t, n) {
	g(t) ? e.type.__ssrInlineRender ? e.ssrRender = t : e.render = t : y(t) && (e.setupState = tn(t)), la(e, n);
}
function la(e, t, n) {
	let r = e.type;
	e.render ||= r.render || i;
	{
		let t = na(e);
		Ye();
		try {
			Tr(e);
		} finally {
			Xe(), t();
		}
	}
}
var ua = { get(e, t) {
	return j(e, "get", ""), e[t];
} };
function da(e) {
	return {
		attrs: new Proxy(e.attrs, ua),
		slots: e.slots,
		emit: e.emit,
		expose: (t) => {
			e.exposed = t || {};
		}
	};
}
function fa(e) {
	return e.exposed ? e.exposeProxy ||= new Proxy(tn(Jt(e.exposed)), {
		get(t, n) {
			if (n in t) return t[n];
			if (n in br) return br[n](e);
		},
		has(e, t) {
			return t in e || t in br;
		}
	}) : e.proxy;
}
function pa(e) {
	return g(e) && "__vccOpts" in e;
}
var $ = (e, t) => /* @__PURE__ */ rn(e, t, aa), ma = "3.5.43", ha = void 0, ga = typeof window < "u" && window.trustedTypes;
if (ga) try {
	ha = /* @__PURE__ */ ga.createPolicy("vue", { createHTML: (e) => e });
} catch {}
var _a = ha ? (e) => ha.createHTML(e) : (e) => e, va = "http://www.w3.org/2000/svg", ya = "http://www.w3.org/1998/Math/MathML", ba = typeof document < "u" ? document : null, xa = ba && /* @__PURE__ */ ba.createElement("template"), Sa = {
	insert: (e, t, n) => {
		t.insertBefore(e, n || null);
	},
	remove: (e) => {
		let t = e.parentNode;
		t && t.removeChild(e);
	},
	createElement: (e, t, n, r) => {
		let i = t === "svg" ? ba.createElementNS(va, e) : t === "mathml" ? ba.createElementNS(ya, e) : n ? ba.createElement(e, { is: n }) : ba.createElement(e);
		return e === "select" && r && r.multiple != null && i.setAttribute("multiple", r.multiple), i;
	},
	createText: (e) => ba.createTextNode(e),
	createComment: (e) => ba.createComment(e),
	setText: (e, t) => {
		e.nodeValue = t;
	},
	setElementText: (e, t) => {
		e.textContent = t;
	},
	parentNode: (e) => e.parentNode,
	nextSibling: (e) => e.nextSibling,
	querySelector: (e) => ba.querySelector(e),
	setScopeId(e, t) {
		e.setAttribute(t, "");
	},
	insertStaticContent(e, t, n, r, i, a) {
		let o = n ? n.previousSibling : t.lastChild;
		if (i && (i === a || i.nextSibling)) for (; t.insertBefore(i.cloneNode(!0), n), i !== a && (i = i.nextSibling););
		else {
			xa.innerHTML = _a(r === "svg" ? `<svg>${e}</svg>` : r === "mathml" ? `<math>${e}</math>` : e);
			let i = xa.content;
			if (r === "svg" || r === "mathml") {
				let e = i.firstChild;
				for (; e.firstChild;) i.appendChild(e.firstChild);
				i.removeChild(e);
			}
			t.insertBefore(i, n);
		}
		return [o ? o.nextSibling : t.firstChild, n ? n.previousSibling : t.lastChild];
	}
}, Ca = /* @__PURE__ */ Symbol("_vtc");
function wa(e, t, n) {
	let r = e[Ca];
	r && (t = (t ? [t, ...r] : [...r]).join(" ")), t == null ? e.removeAttribute("class") : n ? e.setAttribute("class", t) : e.className = t;
}
var Ta = /* @__PURE__ */ Symbol("_vod"), Ea = /* @__PURE__ */ Symbol("_vsh"), Da = /* @__PURE__ */ Symbol(""), Oa = /(?:^|;)\s*display\s*:/;
function ka(e, t, n) {
	let r = e.style, i = _(n), a = !1;
	if (n && !i) {
		if (t) {
			if (_(t)) for (let e of t.split(";")) {
				let t = e.slice(0, e.indexOf(":")).trim();
				n[t] ?? ja(r, t, "");
			}
			else for (let e in t) n[e] ?? ja(r, e, "");
		}
		for (let i in n) {
			i === "display" && (a = !0);
			let o = n[i];
			o == null ? ja(r, i, "") : Fa(e, i, !_(t) && t ? t[i] : void 0, o) || ja(r, i, o);
		}
	} else if (i) {
		if (t !== n) {
			let e = r[Da];
			e && (n += ";" + e), r.cssText = n, a = Oa.test(n);
		}
	} else t && e.removeAttribute("style");
	Ta in e && (e[Ta] = a ? r.display : "", e[Ea] && (r.display = "none"));
}
var Aa = /\s*!important$/;
function ja(e, t, n) {
	if (f(n)) n.forEach((n) => ja(e, t, n));
	else if (n ??= "", t.startsWith("--")) Aa.test(n) ? e.setProperty(t, n.replace(Aa, ""), "important") : e.setProperty(t, n);
	else {
		let r = Pa(e, t);
		Aa.test(n) ? e.setProperty(E(r), n.replace(Aa, ""), "important") : e[r] = n;
	}
}
var Ma = [
	"Webkit",
	"Moz",
	"ms"
], Na = {};
function Pa(e, t) {
	let n = Na[t];
	if (n) return n;
	let r = T(t);
	if (r !== "filter" && r in e) return Na[t] = r;
	r = ae(r);
	for (let n = 0; n < Ma.length; n++) {
		let i = Ma[n] + r;
		if (i in e) return Na[t] = i;
	}
	return t;
}
function Fa(e, t, n, r) {
	return e.tagName === "TEXTAREA" && (t === "width" || t === "height") && _(r) && n === r;
}
var Ia = "http://www.w3.org/1999/xlink";
function La(e, t, n, r, i, a = be(t)) {
	r && t.startsWith("xlink:") ? n == null ? e.removeAttributeNS(Ia, t.slice(6, t.length)) : e.setAttributeNS(Ia, t, n) : n == null || a && !xe(n) ? e.removeAttribute(t) : e.setAttribute(t, a ? "" : v(n) ? String(n) : n);
}
function Ra(e, t, n, r, i) {
	if (t === "innerHTML" || t === "textContent") {
		n != null && (e[t] = t === "innerHTML" ? _a(n) : n);
		return;
	}
	let a = e.tagName;
	if (t === "value" && a !== "PROGRESS" && !a.includes("-")) {
		let r = a === "OPTION" ? e.getAttribute("value") || "" : e.value, i = n == null ? e.type === "checkbox" ? "on" : "" : String(n);
		(r !== i || !("_value" in e)) && (e.value = i), n ?? e.removeAttribute(t), e._value = n;
		return;
	}
	let o = !1;
	if (n === "" || n == null) {
		let r = typeof e[t];
		r === "boolean" ? n = xe(n) : n == null && r === "string" ? (n = "", o = !0) : r === "number" && (n = 0, o = !0);
	}
	try {
		e[t] = n;
	} catch {}
	o && e.removeAttribute(i || t);
}
function za(e, t, n, r) {
	e.addEventListener(t, n, r);
}
function Ba(e, t, n, r) {
	e.removeEventListener(t, n, r);
}
var Va = /* @__PURE__ */ Symbol("_vei");
function Ha(e, t, n, r, i = null) {
	let a = e[Va] || (e[Va] = {}), o = a[t];
	if (r && o) o.value = r;
	else {
		let [n, s] = Ga(t);
		r ? za(e, n, a[t] = Ya(r, i), s) : o && (Ba(e, n, o, s), a[t] = void 0);
	}
}
var Ua = /(Once|Passive|Capture)$/, Wa = /^on:?(?:Once|Passive|Capture)$/;
function Ga(e) {
	let t, n;
	for (; (n = e.match(Ua)) && !Wa.test(e);) t ||= {}, e = e.slice(0, e.length - n[1].length), t[n[1].toLowerCase()] = !0;
	return [e[2] === ":" ? e.slice(3) : E(e.slice(2)), t];
}
var Ka = 0, qa = /* @__PURE__ */ Promise.resolve(), Ja = () => Ka ||= (qa.then(() => Ka = 0), Date.now());
function Ya(e, t) {
	let n = (e) => {
		if (!e._vts) e._vts = Date.now();
		else if (e._vts <= n.attached) return;
		let r = n.value;
		if (f(r)) {
			let n = e.stopImmediatePropagation;
			e.stopImmediatePropagation = () => {
				n.call(e), e._stopped = !0;
			};
			let i = r.slice(), a = [e];
			for (let n = 0; n < i.length && !e._stopped; n++) {
				let e = i[n];
				e && fn(e, t, 5, a);
			}
		} else fn(r, t, 5, [e]);
	};
	return n.value = e, n.attached = Ja(), n;
}
var Xa = (e) => e.charCodeAt(0) === 111 && e.charCodeAt(1) === 110 && e.charCodeAt(2) > 96 && e.charCodeAt(2) < 123, Za = (e, t, n, r, i, a) => {
	let c = i === "svg";
	t === "class" ? wa(e, r, c) : t === "style" ? ka(e, n, r) : o(t) ? s(t) || Ha(e, t, n, r, a) : (t[0] === "." ? (t = t.slice(1), 1) : t[0] === "^" ? (t = t.slice(1), 0) : Qa(e, t, r, c)) ? (Ra(e, t, r), !e.tagName.includes("-") && (t === "value" || t === "checked" || t === "selected") && La(e, t, r, c, a, t !== "value")) : e._isVueCE && ($a(e, t) || e._def.__asyncLoader && (/[A-Z]/.test(t) || !_(r))) ? Ra(e, T(t), r, a, t) : (t === "true-value" ? e._trueValue = r : t === "false-value" && (e._falseValue = r), La(e, t, r, c));
};
function Qa(e, t, n, r) {
	if (r) return !!(t === "innerHTML" || t === "textContent" || t in e && Xa(t) && g(n));
	if (t === "spellcheck" || t === "draggable" || t === "translate" || t === "autocorrect" || t === "sandbox" && e.tagName === "IFRAME" || t === "form" || t === "list" && e.tagName === "INPUT" || t === "type" && e.tagName === "TEXTAREA") return !1;
	if (t === "width" || t === "height") {
		let t = e.tagName;
		if (t === "IMG" || t === "VIDEO" || t === "CANVAS" || t === "SOURCE") return !1;
	}
	return Xa(t) && _(n) ? !1 : t in e;
}
function $a(e, t) {
	let n = e._def.props;
	if (!n) return !1;
	let r = T(t);
	return Array.isArray(n) ? n.some((e) => T(e) === r) : Object.keys(n).some((e) => T(e) === r);
}
var eo = {};
// @__NO_SIDE_EFFECTS__
function to(e, t, n) {
	let r = /* @__PURE__ */ z(e, t);
	w(r) && (r = c({}, r, t));
	class i extends ro {
		constructor(e) {
			super(r, e, n);
		}
	}
	return i.def = r, i;
}
var no = typeof HTMLElement < "u" ? HTMLElement : class {}, ro = class e extends no {
	constructor(e, t = {}, n = fo) {
		super(), this._def = e, this._props = t, this._createApp = n, this._isVueCE = !0, this._instance = null, this._app = null, this._nonce = this._def.nonce, this._connected = !1, this._resolved = !1, this._patching = !1, this._dirty = !1, this._numberProps = null, this._styleChildren = /* @__PURE__ */ new WeakSet(), this._styleAnchors = /* @__PURE__ */ new WeakMap(), this._ob = null, this.shadowRoot && n !== fo ? this._root = this.shadowRoot : e.shadowRoot === !1 ? this._root = this : (this.attachShadow(c({}, e.shadowRootOptions, { mode: "open" })), this._root = this.shadowRoot);
	}
	connectedCallback() {
		if (!this.isConnected) return;
		!this.shadowRoot && !this._resolved && this._parseSlots(), this._connected = !0;
		let t = this;
		for (; t &&= t.assignedSlot || t.parentNode || t.host;) if (t instanceof e) {
			this._parent = t;
			break;
		}
		this._instance || (this._resolved ? this._mount(this._def) : t && t._pendingResolve ? this._pendingResolve = t._pendingResolve.then(() => {
			if (this._pendingResolve = void 0, this.isConnected) return this._resolveDef();
		}) : this._resolveDef());
	}
	_setParent(e = this._parent) {
		e && (this._instance.parent = e._instance, this._inheritParentContext(e));
	}
	_inheritParentContext(e = this._parent) {
		e && this._app && Object.setPrototypeOf(this._app._context.provides, e._instance.provides);
	}
	disconnectedCallback() {
		this._connected = !1, xn(() => {
			this._connected || (this._ob &&= (this._ob.disconnect(), null), this._app && this._app.unmount(), this._instance && (this._instance.ce = void 0), this._app = this._instance = null, this._teleportTargets &&= (this._teleportTargets.clear(), void 0));
		});
	}
	_processMutations(e) {
		for (let t of e) this._setAttr(t.attributeName);
	}
	_resolveDef() {
		if (this._pendingResolve) return this._pendingResolve;
		for (let e = 0; e < this.attributes.length; e++) this._setAttr(this.attributes[e].name);
		this._ob = new MutationObserver(this._processMutations.bind(this)), this._ob.observe(this, { attributes: !0 });
		let e = (e, t = !1) => {
			this._resolved = !0, this._pendingResolve = void 0;
			let { props: n, styles: r } = e, i;
			if (n && !f(n)) for (let e in n) {
				let t = n[e];
				(t === Number || t && t.type === Number) && (e in this._props && (this._props[e] = ue(this._props[e])), (i ||= /* @__PURE__ */ Object.create(null))[T(e)] = !0);
			}
			this._numberProps = i, this._resolveProps(e), this.shadowRoot && this._applyStyles(r), this._mount(e);
		}, t = this._def.__asyncLoader;
		if (t) return this._pendingResolve = t().then((t) => {
			t.configureApp = this._def.configureApp, e(this._def = t, !0);
		}), this._pendingResolve;
		e(this._def);
	}
	_mount(e) {
		this._app = this._createApp(e), this._inheritParentContext(), e.configureApp && e.configureApp(this._app), this._app._ceVNode = this._createVNode(), this._app.mount(this._root);
		let t = this._instance && this._instance.exposed;
		if (t) for (let e in t) d(this, e) || Object.defineProperty(this, e, { get: () => F(t[e]) });
	}
	_resolveProps(e) {
		let { props: t } = e, n = f(t) ? t : Object.keys(t || {});
		for (let e of Object.keys(this)) e[0] !== "_" && n.includes(e) && this._setProp(e, this[e]);
		for (let e of n.map(T)) Object.defineProperty(this, e, {
			get() {
				return this._getProp(e);
			},
			set(t) {
				this._setProp(e, t, !0, !this._patching);
			}
		});
	}
	_setAttr(e) {
		if (e.startsWith("data-v-")) return;
		let t = this.hasAttribute(e), n = t ? this.getAttribute(e) : eo, r = T(e);
		t && this._numberProps && this._numberProps[r] && (n = ue(n)), this._setProp(r, n, !1, !0);
	}
	_getProp(e) {
		return this._props[e];
	}
	_setProp(e, t, n = !0, r = !1) {
		if (t !== this._props[e] && (this._dirty = !0, t === eo ? delete this._props[e] : (this._props[e] = t, e === "key" && this._app && (this._app._ceVNode.key = t)), r && this._instance && this._update(), n)) {
			let n = this._ob;
			n && (this._processMutations(n.takeRecords()), n.disconnect()), t === !0 ? this.setAttribute(E(e), "") : typeof t == "string" || typeof t == "number" ? this.setAttribute(E(e), t + "") : t || this.removeAttribute(E(e)), n && n.observe(this, { attributes: !0 });
		}
	}
	_update() {
		let e = this._createVNode();
		this._app && (e.appContext = this._app._context), uo(e, this._root);
	}
	_createVNode() {
		let e = {};
		this.shadowRoot || (e.onVnodeMounted = e.onVnodeUpdated = this._renderSlots.bind(this));
		let t = Y(this._def, c(e, this._props));
		return this._instance || (t.ce = (e) => {
			this._instance = e, e.ce = this, e.isCE = !0;
			let t = (e, t) => {
				this.dispatchEvent(new CustomEvent(e, w(t[0]) ? c({ detail: t }, t[0]) : { detail: t }));
			};
			e.emit = (e, ...n) => {
				t(e, n), E(e) !== e && t(E(e), n);
			}, this._setParent();
		}), t;
	}
	_applyStyles(e, t, n) {
		if (!e) return;
		if (t) {
			if (t === this._def || this._styleChildren.has(t)) return;
			this._styleChildren.add(t);
		}
		let r = this._nonce, i = this.shadowRoot, a = n ? this._getStyleAnchor(n) || this._getStyleAnchor(this._def) : this._getRootStyleInsertionAnchor(i), o = null;
		for (let s = e.length - 1; s >= 0; s--) {
			let c = document.createElement("style");
			r && c.setAttribute("nonce", r), c.textContent = e[s], i.insertBefore(c, o || a), o = c, s === 0 && (n || this._styleAnchors.set(this._def, c), t && this._styleAnchors.set(t, c));
		}
	}
	_getStyleAnchor(e) {
		if (!e) return null;
		let t = this._styleAnchors.get(e);
		return t && t.parentNode === this.shadowRoot ? t : (t && this._styleAnchors.delete(e), null);
	}
	_getRootStyleInsertionAnchor(e) {
		for (let t = 0; t < e.childNodes.length; t++) {
			let n = e.childNodes[t];
			if (!(n instanceof HTMLStyleElement)) return n;
		}
		return null;
	}
	_parseSlots() {
		let e = this._slots = {}, t;
		for (; t = this.firstChild;) {
			let n = t.nodeType === 1 && t.getAttribute("slot") || "default";
			(e[n] || (e[n] = [])).push(t), this.removeChild(t);
		}
	}
	_renderSlots() {
		let e = this._getSlots(), t = this._instance.type.__scopeId;
		for (let n = 0; n < e.length; n++) {
			let r = e[n], i = r.getAttribute("name") || "default", a = this._slots[i], o = r.parentNode;
			if (a) for (let e of a) {
				if (t && e.nodeType === 1) {
					let n = t + "-s", r = document.createTreeWalker(e, 1);
					e.setAttribute(n, "");
					let i;
					for (; i = r.nextNode();) i.setAttribute(n, "");
				}
				o.insertBefore(e, r);
			}
			else for (; r.firstChild;) o.insertBefore(r.firstChild, r);
			o.removeChild(r);
		}
	}
	_getSlots() {
		let e = [this];
		this._teleportTargets && e.push(...this._teleportTargets);
		let t = /* @__PURE__ */ new Set();
		for (let n of e) {
			let e = n.querySelectorAll("slot");
			for (let n = 0; n < e.length; n++) t.add(e[n]);
		}
		return Array.from(t);
	}
	_injectChildStyle(e, t) {
		this._applyStyles(e.styles, e, t);
	}
	_beginPatch() {
		this._patching = !0, this._dirty = !1;
	}
	_endPatch() {
		this._patching = !1, this._dirty && this._instance && this._update();
	}
	_hasShadowRoot() {
		return this._def.shadowRoot !== !1;
	}
	_removeChildStyle(e) {}
}, io = [
	"ctrl",
	"shift",
	"alt",
	"meta"
], ao = {
	stop: (e) => e.stopPropagation(),
	prevent: (e) => e.preventDefault(),
	self: (e) => e.target !== e.currentTarget,
	ctrl: (e) => !e.ctrlKey,
	shift: (e) => !e.shiftKey,
	alt: (e) => !e.altKey,
	meta: (e) => !e.metaKey,
	left: (e) => "button" in e && e.button !== 0,
	middle: (e) => "button" in e && e.button !== 1,
	right: (e) => "button" in e && e.button !== 2,
	exact: (e, t) => io.some((n) => e[`${n}Key`] && !t.includes(n))
}, oo = (e, t) => {
	if (!e) return e;
	let n = e._withMods ||= {}, r = t.join(".");
	return n[r] || (n[r] = ((n, ...r) => {
		for (let e = 0; e < t.length; e++) {
			let r = ao[t[e]];
			if (r && r(n, t)) return;
		}
		return e(n, ...r);
	}));
}, so = /* @__PURE__ */ c({ patchProp: Za }, Sa), co;
function lo() {
	return co ||= vi(so);
}
var uo = ((...e) => {
	lo().render(...e);
}), fo = ((...e) => {
	let t = lo().createApp(...e), { mount: n } = t;
	return t.mount = (e) => {
		let r = mo(e);
		if (!r) return;
		let i = t._component;
		!g(i) && !i.render && !i.template && (i.template = r.innerHTML), r.nodeType === 1 && (r.textContent = "");
		let a = n(r, !1, po(r));
		return r instanceof Element && (r.removeAttribute("v-cloak"), r.setAttribute("data-v-app", "")), a;
	}, t;
});
function po(e) {
	if (e instanceof SVGElement) return "svg";
	if (typeof MathMLElement == "function" && e instanceof MathMLElement) return "mathml";
}
function mo(e) {
	return _(e) ? document.querySelector(e) : e;
}
//#endregion
//#region src/elements/define.ts
function ho(e) {
	let t = customElements.get(e.tag);
	if (t) return t;
	let n = e.component, r = /* @__PURE__ */ to(n, { shadowRoot: !1 });
	return customElements.define(e.tag, r), r;
}
function go(e) {
	return e;
}
function _o(e, t) {
	return t ? e.replace(/\{(\w+)\}/g, (e, n) => {
		let r = t[n];
		return r === void 0 ? e : String(r);
	}) : e;
}
function vo(e, t, n, r) {
	return _o((t === "en" ? e.en[n] : void 0) ?? e.de[n] ?? n, r);
}
var yo = "de", bo = /* @__PURE__ */ new Set();
function xo() {
	return yo;
}
function So(e) {
	return bo.add(e), () => bo.delete(e);
}
//#endregion
//#region ../ui-core/src/store.ts
function Co(e, t) {
	return Object.keys(t).some((n) => !Object.is(e[n], t[n]));
}
function wo(e) {
	let t = e, n = /* @__PURE__ */ new Set();
	return {
		get: () => t,
		set(e) {
			let r = typeof e == "function" ? e(t) : e;
			if (Co(t, r)) {
				t = {
					...t,
					...r
				};
				for (let e of [...n]) e();
			}
		},
		subscribe(e) {
			return n.add(e), () => n.delete(e);
		}
	};
}
var To = {
	busy: null,
	error: null,
	notice: ""
};
function Eo(e, t, n, r) {
	return async function(i, a) {
		let o = t();
		if (!o) return null;
		e.set({
			busy: i,
			error: null
		});
		try {
			return await a(o);
		} catch (t) {
			let i = n(t);
			return e.set({ error: i }), r?.(i), null;
		} finally {
			e.set({ busy: null });
		}
	};
}
//#endregion
//#region ../ui-core/src/base/icons.ts
var Do = {
	close: ["M6 6l12 12", "M18 6L6 18"],
	plus: ["M12 5v14", "M5 12h14"],
	minus: ["M5 12h14"],
	check: ["M5 12.5l4.5 4.5L19 7.5"],
	search: ["M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13z", "M15.5 15.5L20 20"],
	filter: [
		"M4 5h16",
		"M7 12h10",
		"M10 19h4"
	],
	settings: [
		"M4 6h9",
		"M17 6h3",
		"M15 4v4",
		"M4 12h3",
		"M11 12h9",
		"M9 10v4",
		"M4 18h11",
		"M19 18h1",
		"M17 16v4"
	],
	share: [
		"M6 14a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
		"M18 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
		"M18 21a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
		"M8.2 10.4l7.6-4.3",
		"M8.2 12.6l7.6 4.3"
	],
	trash: [
		"M4 7h16",
		"M9 7V4.5h6V7",
		"M6.5 7l1 13h9l1-13",
		"M10 11v6",
		"M14 11v6"
	],
	edit: ["M4 20h4L19 9l-4-4L4 16v4z", "M13.5 6.5l4 4"],
	"chevron-down": ["M6 9l6 6 6-6"],
	"chevron-up": ["M6 15l6-6 6 6"],
	"chevron-left": ["M15 6l-6 6 6 6"],
	"chevron-right": ["M9 6l6 6-6 6"],
	sort: [
		"M8 4v16",
		"M4.5 7.5L8 4l3.5 3.5",
		"M16 20V4",
		"M12.5 16.5L16 20l3.5-3.5"
	],
	"sort-asc": ["M12 19V5", "M6.5 10.5L12 5l5.5 5.5"],
	"sort-desc": ["M12 5v14", "M6.5 13.5L12 19l5.5-5.5"],
	grip: [
		"M9 6h.01",
		"M15 6h.01",
		"M9 12h.01",
		"M15 12h.01",
		"M9 18h.01",
		"M15 18h.01"
	],
	calendar: [
		"M4.5 6.5h15v13h-15z",
		"M4.5 10.5h15",
		"M8.5 4v4",
		"M15.5 4v4"
	],
	clock: ["M12 20.5a8.5 8.5 0 1 0 0-17 8.5 8.5 0 0 0 0 17z", "M12 7.5V12l3 2"],
	paperclip: ["M19 11.5l-7.2 7.2a4.5 4.5 0 0 1-6.4-6.4l7.8-7.8a3 3 0 0 1 4.2 4.2l-7.6 7.6a1.5 1.5 0 0 1-2.1-2.1l6.9-6.9"],
	user: ["M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z", "M4.5 20.5a7.5 7.5 0 0 1 15 0"],
	lock: ["M6 11h12v9H6z", "M8.5 11V8a3.5 3.5 0 0 1 7 0v3"],
	pin: ["M9 4h6l-1 6 3 3H7l3-3-1-6z", "M12 13v7"],
	sun: [
		"M12 16.5a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9z",
		"M12 2.5v2",
		"M12 19.5v2",
		"M2.5 12h2",
		"M19.5 12h2",
		"M5.3 5.3l1.4 1.4",
		"M17.3 17.3l1.4 1.4",
		"M5.3 18.7l1.4-1.4",
		"M17.3 6.7l1.4-1.4"
	],
	moon: ["M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z"],
	warning: [
		"M12 4l9 16H3z",
		"M12 10v4.5",
		"M12 17.5h.01"
	],
	info: [
		"M12 20.5a8.5 8.5 0 1 0 0-17 8.5 8.5 0 0 0 0 17z",
		"M12 11v5.5",
		"M12 7.5h.01"
	],
	expand: [
		"M4 9V4h5",
		"M20 9V4h-5",
		"M4 15v5h5",
		"M20 15v5h-5"
	],
	"more-vertical": [
		"M12 5.5h.01",
		"M12 12h.01",
		"M12 18.5h.01"
	]
};
//#endregion
//#region ../common/src/http/error.ts
function Oo(e) {
	return typeof e == "object" && !!e;
}
function ko(e) {
	return typeof e == "string" && e.trim() !== "" ? e.trim() : null;
}
function Ao(e) {
	return Array.isArray(e) ? e.filter((e, t) => !(t === 0 && [
		"body",
		"query",
		"path",
		"header"
	].includes(String(e)))).map(String).join(".") : "";
}
function jo(e) {
	if (!Oo(e)) return ko(e);
	let t = ko(e.msg) ?? ko(e.message);
	if (!t) return null;
	let n = Ao(e.loc);
	return n ? `${n}: ${t}` : t;
}
function Mo(e) {
	if (Array.isArray(e)) {
		let t = e.map(jo).filter((e) => e !== null);
		return t.length > 0 ? t.join("; ") : null;
	}
	return Oo(e) ? ko(e.message) ?? ko(e.msg) : ko(e);
}
function No(e) {
	if (!Oo(e)) return ko(e);
	let t = Oo(e.error) ? ko(e.error.message) : ko(e.error);
	return Mo(e.detail) ?? t ?? ko(e.message);
}
//#endregion
//#region ../common/src/http/rest.ts
var Po = class extends Error {
	status;
	code;
	constructor(e, t, n) {
		super(e), this.status = t, this.code = n, this.name = "RestError";
	}
};
function Fo(e, t) {
	return `${e.baseUrl.replace(/\/$/, "")}${t}`;
}
async function Io(e, t, n) {
	let r = e.fetch ?? ((e, t) => globalThis.fetch(e, t)), i = n === void 0 ? {
		method: "GET",
		headers: {
			Accept: "application/json",
			...e.headers
		}
	} : {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Accept: "application/json",
			...e.headers
		},
		body: JSON.stringify(n)
	}, a = await r(Fo(e, t), i);
	if (a.ok) return a;
	throw await Lo(a);
}
async function Lo(e) {
	try {
		let t = await e.json();
		return new Po(t.error?.message ?? No(t) ?? `HTTP ${e.status}`, e.status, t.error?.code ?? "http_error");
	} catch {
		return new Po(`HTTP ${e.status}`, e.status, "http_error");
	}
}
async function Ro(e, t, n) {
	return await (await Io(e, t, n)).json();
}
//#endregion
//#region ../ui-core/src/runner/messages.ts
var zo = go({
	de: {
		title: "Runner-Konsole",
		loading: "Daten werden geladen …",
		working: "Wird ausgeführt …",
		failed: "Anfrage abgelehnt: {message}",
		tabs: "Bereiche",
		tabStatus: "Status",
		tabEinstellungen: "Einstellungen",
		tabWerkzeuge: "Werkzeuge",
		tabPrioritaeten: "Prioritäten",
		meta: "{rechner} · Profilversion {version}",
		syncAus: "nur lokal verwaltet",
		syncZentral: "Abgleich mit {sync}",
		nurLesen: "Nur lesen: Änderungen sind nur direkt auf dem Rechner möglich.",
		refresh: "Aktualisieren",
		ueberblick: "Überblick",
		ziel: "Ziel",
		sollQuelle: "Soll-Quelle",
		profilVersion: "Profilversion",
		aenderung: "Letzte Änderung",
		aenderungWert: "{zeit} · {quelle}",
		aenderungKeine: "noch keine",
		image: "Runner-Image",
		netzsperre: "Netzsperre",
		kontingent: "GitHub-Kontingent",
		runnerVersion: "Runner-Version",
		runnerVersionFrist: "{version}, aktualisieren bis {frist}",
		vorhanden: "vorhanden",
		fehlt: "fehlt",
		aktiv: "aktiv",
		inaktiv: "nicht aktiv",
		unbekannt: "unbekannt",
		klassen: "Runner-Klassen",
		keineKlassen: "Keine Runner-Klassen im Profil.",
		spalteKlasse: "Klasse",
		spalteSoll: "Soll",
		spalteMax: "Max.",
		spalteInstanzen: "Instanzen",
		spalteRegistriert: "Registriert",
		spalteBelegt: "Belegt",
		spalteWarteschlange: "Warteschlange",
		spalteGruende: "Begründung",
		hardware: "Hardware",
		hinweisUnbekannt: "Unbekannte Runner registriert: {namen}",
		hinweisImage: "Das Runner-Image fehlt.",
		hinweisNetzsperre: "Die Netzsperre ist nicht aktiv.",
		abschnittAllgemein: "Allgemein",
		abschnittRegelung: "Regelung",
		abschnittThermik: "Thermikquelle",
		abschnittNetz: "Netz",
		abschnittKlasse: "Klasse {name}",
		abschnittKarte: "Grafikkarte {index}: {name}",
		fSollQuelle: "Soll-Quelle",
		fSollDatei: "Soll-Datei",
		fBackend: "Backend",
		fImage: "Runner-Image",
		fReserveCpus: "Reserve für den Rechner: CPUs",
		fReserveSpeicher: "Reserve für den Rechner: Speicher (GB)",
		fVorrang: "Vorrang interaktiver Nutzung",
		fLeerlauf: "Leerlauf bis zur vollen Leistung (Minuten)",
		fAnteil: "Anteil der Runner bei Nutzung (0–1)",
		fSwap: "Swap-Sperre ab (GB, 0 = aus)",
		fRam: "Mindestens frei: RAM (GB)",
		fLast: "Höchstlast je Kern",
		fTemperatur: "Höchsttemperatur (°C)",
		fVon: "Volle Leistung ab (Uhr, 0 = aus)",
		fBis: "Volle Leistung bis (Uhr)",
		fHaltezeit: "Haltezeit gegen Flattern (s)",
		fThermikAktiv: "Thermikquelle nutzen",
		fThermikUrl: "Adresse der Thermikquelle (URL)",
		fNetzAktiv: "Eigenes Docker-Netz",
		fSperre: "Netzsperre verlangen",
		kArt: "Art",
		oCpu: "CPU",
		oGpu: "GPU (Grafikkarte)",
		klasseName: "Name der Klasse",
		umbenennen: "Umbenennen",
		neueKlasse: "Neue Klasse",
		hinzufuegen: "Klasse hinzufügen",
		klasseNameUngueltig: "Klassenname: a–z, 0–9, Bindestrich, höchstens 31 Zeichen",
		klasseNameVergeben: "Dieser Name ist bereits vergeben.",
		anmeldung: "Anmeldung bei GitHub",
		kAktiv: "Aktiv",
		kMin: "Mindestanzahl",
		kMax: "Höchstanzahl",
		kLeise: "Höchstanzahl im Leisemodus (−1 = wie Höchstanzahl)",
		kCpus: "CPUs je Runner",
		kSpeicher: "Speicher je Runner (GB)",
		kVram: "Grafikspeicher je Runner (MB)",
		kLabels: "Labels (durch Komma getrennt)",
		gErlaubt: "Für Runner erlaubt",
		gKlasse: "Klasse",
		oStatisch: "statisch (Profil)",
		oLokal: "lokal (eingebauter Regler)",
		oDatei: "Datei (externer Regler)",
		pruefen: "Prüfen",
		anwenden: "Anwenden",
		verwerfen: "Verwerfen",
		ungespeichert: "Nicht angewendete Änderungen",
		gueltig: "gültig",
		ungueltig: "fehlerhaft",
		probleme: "Fehler im Profil",
		vorschau: "Vorschau der Änderungen",
		keineAenderung: "Keine Dateiänderungen.",
		schritte: "Schritte beim Anwenden",
		rootBefehl: "Einmal als root ausführen (zum Kopieren markieren):",
		angewendet: "Profil angewendet (Version {version}).",
		nichtAngewendet: "Nicht angewendet: {meldung}",
		konflikt: "Konflikt, nichts angewendet. {meldung}",
		konfliktFeld: "Feld",
		konfliktEntwurf: "Ihr Entwurf",
		konfliktGespeichert: "Gespeichert ({quelle})",
		gespeichertUebernehmen: "Gespeicherten Stand übernehmen",
		entwurfAnwenden: "Entwurf trotzdem anwenden",
		werkzeugProfil: "Prüfprofil {name}",
		spalteWerkzeug: "Werkzeug",
		spalteBereich: "Bereich",
		spalteImage: "Im Image",
		spalteAktiv: "Aktiv",
		spalteZeitlimit: "Zeitlimit (s)",
		spaltePrioritaet: "Priorität",
		nichtInstalliert: "nicht installiert",
		speichern: "Speichern",
		gespeichert: "Werkzeug-Einstellungen gespeichert.",
		keineWerkzeuge: "Keine Werkzeuge im Katalog.",
		prioritaetenHinweis: "Rang 1 hat Vorrang. Bei knapper Kapazität weichen verdrängbare Einträge von unten nach oben.",
		keinePrioritaeten: "Keine Prioritäten festgelegt.",
		rang: "Rang {rang}",
		hoch: "Nach oben: {name}",
		runter: "Nach unten: {name}",
		verdraengbar: "Verdrängbar",
		mindestens: "Mindestens",
		weichtZuerst: "Bei Platzmangel weicht zuerst: {name}",
		keinerVerdraengbar: "Kein Eintrag ist verdrängbar."
	},
	en: {
		title: "Runner console",
		loading: "Loading …",
		working: "Working …",
		failed: "Request rejected: {message}",
		tabs: "Sections",
		tabStatus: "Status",
		tabEinstellungen: "Settings",
		tabWerkzeuge: "Tools",
		tabPrioritaeten: "Priorities",
		meta: "{rechner} · profile version {version}",
		syncAus: "managed locally only",
		syncZentral: "synchronised with {sync}",
		nurLesen: "Read only: changes are only possible on the machine itself.",
		refresh: "Refresh",
		ueberblick: "Overview",
		ziel: "Target",
		sollQuelle: "Target source",
		profilVersion: "Profile version",
		aenderung: "Last change",
		aenderungWert: "{zeit} · {quelle}",
		aenderungKeine: "none yet",
		image: "Runner image",
		netzsperre: "Network lock",
		kontingent: "GitHub quota",
		runnerVersion: "Runner version",
		runnerVersionFrist: "{version}, update by {frist}",
		vorhanden: "present",
		fehlt: "missing",
		aktiv: "active",
		inaktiv: "not active",
		unbekannt: "unknown",
		klassen: "Runner classes",
		keineKlassen: "No runner classes in the profile.",
		spalteKlasse: "Class",
		spalteSoll: "Target",
		spalteMax: "Max.",
		spalteInstanzen: "Instances",
		spalteRegistriert: "Registered",
		spalteBelegt: "Busy",
		spalteWarteschlange: "Queue",
		spalteGruende: "Reason",
		hardware: "Hardware",
		hinweisUnbekannt: "Unknown runners registered: {namen}",
		hinweisImage: "The runner image is missing.",
		hinweisNetzsperre: "The network lock is not active.",
		abschnittAllgemein: "General",
		abschnittRegelung: "Scaling",
		abschnittThermik: "Thermal source",
		abschnittNetz: "Network",
		abschnittKlasse: "Class {name}",
		abschnittKarte: "Graphics card {index}: {name}",
		fSollQuelle: "Target source",
		fSollDatei: "Target file",
		fBackend: "Backend",
		fImage: "Runner image",
		fReserveCpus: "Reserve for the machine: CPUs",
		fReserveSpeicher: "Reserve for the machine: memory (GB)",
		fVorrang: "Priority for interactive use",
		fLeerlauf: "Idle time until full power (minutes)",
		fAnteil: "Share of runners while in use (0–1)",
		fSwap: "Swap lock from (GB, 0 = off)",
		fRam: "Minimum free RAM (GB)",
		fLast: "Maximum load per core",
		fTemperatur: "Maximum temperature (°C)",
		fVon: "Full power from (hour, 0 = off)",
		fBis: "Full power until (hour)",
		fHaltezeit: "Hold time against flapping (s)",
		fThermikAktiv: "Use thermal source",
		fThermikUrl: "Thermal source address (URL)",
		fNetzAktiv: "Dedicated Docker network",
		fSperre: "Require network lock",
		kArt: "Kind",
		oCpu: "CPU",
		oGpu: "GPU (graphics card)",
		klasseName: "Class name",
		umbenennen: "Rename",
		neueKlasse: "New class",
		hinzufuegen: "Add class",
		klasseNameUngueltig: "Class name: a–z, 0–9, hyphen, at most 31 characters",
		klasseNameVergeben: "This name is already taken.",
		anmeldung: "GitHub sign-in",
		kAktiv: "Active",
		kMin: "Minimum",
		kMax: "Maximum",
		kLeise: "Maximum in quiet mode (−1 = same as maximum)",
		kCpus: "CPUs per runner",
		kSpeicher: "Memory per runner (GB)",
		kVram: "GPU memory per runner (MB)",
		kLabels: "Labels (comma separated)",
		gErlaubt: "Allowed for runners",
		gKlasse: "Class",
		oStatisch: "static (profile)",
		oLokal: "local (built-in regulator)",
		oDatei: "file (external regulator)",
		pruefen: "Check",
		anwenden: "Apply",
		verwerfen: "Discard",
		ungespeichert: "Changes not yet applied",
		gueltig: "valid",
		ungueltig: "invalid",
		probleme: "Errors in the profile",
		vorschau: "Preview of changes",
		keineAenderung: "No file changes.",
		schritte: "Steps when applying",
		rootBefehl: "Run once as root (select to copy):",
		angewendet: "Profile applied (version {version}).",
		nichtAngewendet: "Not applied: {meldung}",
		konflikt: "Conflict, nothing applied. {meldung}",
		konfliktFeld: "Field",
		konfliktEntwurf: "Your draft",
		konfliktGespeichert: "Saved ({quelle})",
		gespeichertUebernehmen: "Take saved version",
		entwurfAnwenden: "Apply draft anyway",
		werkzeugProfil: "Check profile {name}",
		spalteWerkzeug: "Tool",
		spalteBereich: "Area",
		spalteImage: "In image",
		spalteAktiv: "Active",
		spalteZeitlimit: "Time limit (s)",
		spaltePrioritaet: "Priority",
		nichtInstalliert: "not installed",
		speichern: "Save",
		gespeichert: "Tool settings saved.",
		keineWerkzeuge: "No tools in the catalogue.",
		prioritaetenHinweis: "Rank 1 wins. When capacity is short, preemptible entries give way from the bottom up.",
		keinePrioritaeten: "No priorities defined.",
		rang: "Rank {rang}",
		hoch: "Move up: {name}",
		runter: "Move down: {name}",
		verdraengbar: "Preemptible",
		mindestens: "Minimum",
		weichtZuerst: "Gives way first: {name}",
		keinerVerdraengbar: "No entry is preemptible."
	}
}), Bo = { "X-Auditcore-Runner": "1" }, Vo = "auditcore-runner/werkzeuge/1";
function Ho(e) {
	let t = e ?? ((e, t) => globalThis.fetch(e, t));
	return async (e, n) => {
		let r = await t(e, n);
		if (r.ok) return r;
		let i = await r.clone().json().catch(() => null), a = typeof i == "object" && i ? i.fehler : void 0;
		return typeof a == "string" ? new Response(JSON.stringify({ error: {
			code: `http_${r.status}`,
			message: a
		} }), {
			status: r.status,
			headers: { "Content-Type": "application/json" }
		}) : r;
	};
}
function Uo(e) {
	let t = {
		...e,
		fetch: Ho(e.fetch)
	}, n = {
		...t,
		headers: {
			...t.headers,
			...Bo
		}
	};
	return {
		status: () => Ro(t, "/status"),
		profil: () => Ro(t, "/profil"),
		pruefen: (e) => Ro(n, "/profil/pruefen", { profil: e }),
		async anwenden(e, t) {
			try {
				return await Ro(n, "/profil/anwenden", {
					profil: e,
					erwartete_version: t
				});
			} catch (e) {
				if (e instanceof Po && e.status === 409) return {
					gueltig: !0,
					probleme: [],
					aktive_version: null,
					aenderungen: [],
					schritte: [],
					netzsperre_befehl: null,
					angewendet: !1,
					konflikt: !0,
					meldung: e.message
				};
				throw e;
			}
		},
		werkzeuge: () => Ro(t, "/werkzeuge"),
		async werkzeugeSpeichern(e) {
			await Ro(n, "/werkzeuge", {
				schema: Vo,
				profile: e
			});
		}
	};
}
//#endregion
//#region ../ui-core/src/runner/profil.ts
var Wo = /* @__PURE__ */ new Set(["version", "aenderung"]);
function Go(e) {
	return typeof e == "object" && !!e && !Array.isArray(e);
}
function Ko(e, t) {
	let n = e;
	for (let e of t) if (Array.isArray(n) && typeof e == "number") n = n[e];
	else if (Go(n) && typeof e == "string") n = n[e];
	else return;
	return n;
}
function qo(e, t, n) {
	if (t.length === 0) return n;
	let [r, ...i] = t;
	if (typeof r == "number") {
		let t = Array.isArray(e) ? [...e] : [];
		return t[r] = qo(t[r], i, n), t;
	}
	let a = Go(e) ? { ...e } : {};
	return a[r] = qo(a[r], i, n), a;
}
function Jo(e, t, n) {
	return qo(e, t, n);
}
function Yo(e, t, n) {
	if (Go(e)) {
		for (let [r, i] of Object.entries(e)) (t || !Wo.has(r)) && Yo(i, t ? `${t}.${r}` : r, n);
		return;
	}
	n.set(t, JSON.stringify(e ?? null));
}
function Xo(e, t) {
	let n = /* @__PURE__ */ new Map(), r = /* @__PURE__ */ new Map();
	return Yo(e, "", n), Yo(t, "", r), [.../* @__PURE__ */ new Set([...n.keys(), ...r.keys()])].sort().filter((e) => n.get(e) !== r.get(e)).map((e) => ({
		pfad: e,
		entwurf: n.get(e) ?? "–",
		gespeichert: r.get(e) ?? "–"
	}));
}
function Zo(e, t) {
	return !e || !t ? !1 : Xo(e, t).length > 0;
}
function Qo(e) {
	let t = Ko(e, ["version"]);
	return typeof t == "number" ? t : 0;
}
function $o(e) {
	let t = Ko(e, ["prioritaeten"]);
	return Array.isArray(t) ? t.filter(Go).map((e) => ({
		klasse: String(e.klasse ?? ""),
		rang: typeof e.rang == "number" ? e.rang : 0,
		verdraengbar: e.verdraengbar !== !1,
		min: typeof e.min == "number" ? e.min : 0
	})).sort((e, t) => e.rang - t.rang || e.klasse.localeCompare(t.klasse)) : [];
}
function es(e, t, n) {
	let r = $o(e), i = t + n;
	if (t < 0 || i < 0 || i >= r.length) return e;
	let a = [...r];
	return [a[t], a[i]] = [a[i], a[t]], Jo(e, ["prioritaeten"], a.map((e, t) => ({
		...e,
		rang: t + 1
	})));
}
function ts(e, t, n) {
	let r = $o(e);
	return r[t] ? Jo(e, ["prioritaeten"], r.map((e, r) => r === t ? {
		...e,
		...n
	} : e)) : e;
}
function ns(e) {
	return [...e].reverse().find((e) => e.verdraengbar) ?? null;
}
var rs = /^[a-z0-9][a-z0-9-]{0,30}$/;
function is(e) {
	let t = Ko(e, ["klassen"]);
	return Go(t) ? Object.keys(t).sort() : [];
}
function as(e, t) {
	return Ko(e, [
		"klassen",
		t,
		"art"
	]) === "gpu" ? "gpu" : "cpu";
}
function os(e, t, n) {
	return rs.test(t) ? t !== n && is(e).includes(t) ? "vergeben" : null : "ungueltig";
}
function ss(e, t) {
	return os(e, t) ? e : Jo(e, ["klassen", t], {
		art: "cpu",
		aktiv: !0,
		cpus: 2,
		speicher_gb: 4,
		min_instanzen: 0,
		max_instanzen: 1,
		leise_max: -1,
		vram_mb: 0,
		labels: [
			"self-hosted",
			"linux",
			"x64",
			t
		]
	});
}
function cs(e, t, n) {
	let r = Ko(e, ["klassen"]);
	if (t === n || !Go(r) || !(t in r) || os(e, n, t)) return e;
	let i = r[t], a = Ko(i, ["labels"]), o = Go(i) && Array.isArray(a) ? {
		...i,
		labels: a.map((e) => e === t ? n : e)
	} : i, s = Jo(e, ["klassen"], Object.fromEntries(Object.entries(r).map(([e, r]) => e === t ? [n, o] : [e, r])));
	for (let e of ["gpus", "prioritaeten"]) {
		let r = Ko(s, [e]);
		Array.isArray(r) && (s = Jo(s, [e], r.map((e) => Go(e) && e.klasse === t ? {
			...e,
			klasse: n
		} : e)));
	}
	return s;
}
//#endregion
//#region ../ui-core/src/runner/eingabe.ts
function ls(e, t) {
	if (e === "schalter") return !!t;
	let n = String(t);
	if (e === "zahl") {
		let e = Number(n.replace(",", "."));
		return n.trim() !== "" && Number.isFinite(e) ? e : n;
	}
	return e === "liste" ? n.split(",").map((e) => e.trim()).filter(Boolean) : n;
}
function us(e, t, n) {
	return `werkzeug:${e}:${t}:${n}`;
}
//#endregion
//#region ../ui-core/src/runner/aktionen.ts
function ds(e, t) {
	e.set({
		stand: t,
		entwurf: t.profil,
		pruefung: null,
		konflikt: null,
		eingaben: {},
		klassenNamen: {},
		neueKlasse: ""
	});
}
function fs(e, t) {
	let n = e.get().entwurf;
	n && e.set({
		entwurf: t(n),
		pruefung: null,
		meldung: null
	});
}
async function ps({ store: e, run: t }, n, r) {
	let i = await t("anwenden", (e) => e.profil());
	i && e.set({
		pruefung: null,
		konflikt: {
			gespeichert: i,
			meldung: r.meldung ?? "",
			unterschiede: Xo(n, i.profil)
		}
	});
}
async function ms({ store: e, run: t, applied: n }, r, i) {
	let a = await t("load", (e) => Promise.all([e.status(), e.profil()]));
	a && (ds(e, a[1]), e.set({ status: a[0] })), e.set({
		pruefung: r,
		meldung: {
			key: "angewendet",
			params: { version: i },
			ton: "success"
		}
	}), n(i);
}
async function hs(e, t) {
	let { store: n, run: r } = e, i = n.get().entwurf;
	if (!i) return;
	n.set({ meldung: null });
	let a = await r("anwenden", (e) => e.anwenden(i, t));
	if (a) {
		if (a.konflikt) return ps(e, i, a);
		if (!a.angewendet) {
			n.set({
				pruefung: a,
				meldung: {
					key: "nichtAngewendet",
					params: { meldung: a.meldung ?? "" },
					ton: "warning"
				}
			});
			return;
		}
		return ms(e, a, a.version ?? t + 1);
	}
}
function gs(e) {
	let { store: t, run: n } = e;
	return {
		setze: (e, n) => fs(t, (t) => Jo(t, e, n)),
		eingabe(e, n, r) {
			typeof r == "string" && t.set({ eingaben: {
				...t.get().eingaben,
				[e.join(".")]: r
			} }), fs(t, (t) => {
				let i = Jo(t, e, ls(n, r));
				return e.length === 3 && e[0] === "klassen" && e[2] === "art" && r === "cpu" ? Jo(i, [
					"klassen",
					e[1],
					"vram_mb"
				], 0) : i;
			});
		},
		verwerfen() {
			let e = t.get().stand;
			e && ds(t, e), t.set({ meldung: null });
		},
		async pruefen() {
			let e = t.get().entwurf;
			if (!e) return;
			t.set({ meldung: null });
			let r = await n("pruefen", (t) => t.pruefen(e));
			r && t.set({ pruefung: r });
		},
		anwenden: () => hs(e, Qo(t.get().stand?.profil)),
		gespeichertUebernehmen() {
			let e = t.get().konflikt;
			e && ds(t, e.gespeichert);
		},
		async entwurfTrotzdemAnwenden() {
			let n = t.get().konflikt;
			n && (t.set({
				stand: n.gespeichert,
				konflikt: null
			}), await hs(e, Qo(n.gespeichert.profil)));
		},
		verschiebe: (e, n) => fs(t, (t) => es(t, e, n)),
		prioritaet: (e, n) => fs(t, (t) => ts(t, e, n))
	};
}
function _s({ store: e, run: t }) {
	return {
		werkzeug(t, n, r) {
			let i = e.get().werkzeugEntwurf, a = i?.[t]?.[n];
			i && a && e.set({
				werkzeugEntwurf: {
					...i,
					[t]: {
						...i[t],
						[n]: {
							...a,
							...r
						}
					}
				},
				meldung: null
			});
		},
		werkzeugZahl(t, n, r, i) {
			let a = Number(i);
			e.set({ eingaben: {
				...e.get().eingaben,
				[us(t, n, r)]: i
			} }), i.trim() !== "" && Number.isInteger(a) && a >= 0 && this.werkzeug(t, n, { [r]: a });
		},
		async werkzeugeSpeichern() {
			let n = e.get().werkzeugEntwurf;
			if (!n || !await t("werkzeuge", async (e) => (await e.werkzeugeSpeichern(n), !0))) return;
			let r = e.get().werkzeuge;
			e.set({
				werkzeuge: r && {
					...r,
					profile: n
				},
				meldung: {
					key: "gespeichert",
					ton: "success"
				}
			});
		}
	};
}
function vs({ store: e }) {
	return {
		neueKlasseEingabe: (t) => e.set({ neueKlasse: t }),
		klasseHinzufuegen() {
			let { entwurf: t, neueKlasse: n } = e.get(), r = n.trim();
			t && !os(t, r) && (fs(e, (e) => ss(e, r)), e.set({ neueKlasse: "" }));
		},
		klassenNameEingabe: (t, n) => e.set({ klassenNamen: {
			...e.get().klassenNamen,
			[t]: n
		} }),
		klasseUmbenennen(t) {
			let { entwurf: n, klassenNamen: r } = e.get(), i = (r[t] ?? t).trim();
			if (!n || i === t || os(n, i, t)) return;
			let a = Object.fromEntries(Object.entries(r).filter(([e]) => e !== t));
			fs(e, (e) => cs(e, t, i)), e.set({ klassenNamen: a });
		}
	};
}
//#endregion
//#region ../ui-core/src/runner/controller.ts
var ys = {
	...To,
	ansicht: "status",
	status: null,
	stand: null,
	entwurf: null,
	pruefung: null,
	konflikt: null,
	werkzeuge: null,
	werkzeugEntwurf: null,
	meldung: null,
	eingaben: {},
	klassenNamen: {},
	neueKlasse: ""
}, bs = [
	"status",
	"einstellungen",
	"werkzeuge",
	"prioritaeten"
], xs = (e) => e instanceof Error ? e.message : String(e);
function Ss(e) {
	let t = e.port();
	if (t) return t;
	let n = e.api?.();
	return n ? Uo({ baseUrl: n }) : null;
}
function Cs(e) {
	let t = wo({ ...ys }), n = Eo(t, () => Ss(e), xs, (t) => e.callbacks?.().failed?.(t)), r = {
		store: t,
		run: n,
		applied: (t) => e.callbacks?.().applied?.(t)
	};
	return {
		store: t,
		async load() {
			let e = await n("load", (e) => Promise.all([
				e.status(),
				e.profil(),
				e.werkzeuge()
			]));
			if (!e) return;
			let [r, i, a] = e;
			t.set({
				status: r,
				werkzeuge: a,
				werkzeugEntwurf: a.profile,
				stand: i,
				entwurf: i.profil,
				pruefung: null,
				konflikt: null,
				eingaben: {},
				klassenNamen: {},
				neueKlasse: ""
			});
		},
		zeige(e) {
			t.set({ ansicht: e });
		},
		...gs(r),
		..._s(r),
		...vs(r)
	};
}
//#endregion
//#region ../ui-core/src/runner/view.ts
var ws = {
	status: "tabStatus",
	einstellungen: "tabEinstellungen",
	werkzeuge: "tabWerkzeuge",
	prioritaeten: "tabPrioritaeten"
};
function Ts(e, t) {
	return bs.map((n) => ({
		id: n,
		label: t(ws[n]),
		selected: e.ansicht === n
	}));
}
function Es(e, t) {
	return bs[(bs.indexOf(e) + t + bs.length) % bs.length];
}
function Ds(e) {
	return !!(e.status?.nur_lesen || e.stand?.nur_lesen);
}
function Os(e) {
	return Zo(e.entwurf, e.stand?.profil ?? null);
}
function ks(e, t) {
	let n = e.status;
	if (!n) return "";
	let r = !n.sync || n.sync === "aus" ? t("syncAus") : t("syncZentral", { sync: n.sync });
	return `${t("meta", {
		rechner: n.rechner,
		version: n.profil_version
	})} · ${r}`;
}
function As(e, t) {
	let n = e.status, r = [];
	return Ds(e) && r.push({
		ton: "info",
		text: t("nurLesen")
	}), n ? (n.unbekannte_runner?.length && r.push({
		ton: "danger",
		text: t("hinweisUnbekannt", { namen: n.unbekannte_runner.join(", ") })
	}), n.image_vorhanden || r.push({
		ton: "warning",
		text: t("hinweisImage")
	}), n.netzsperre_aktiv === !1 && r.push({
		ton: "warning",
		text: t("hinweisNetzsperre")
	}), r) : r;
}
function js(e, t, n, r) {
	return e == null ? r("unbekannt") : e ? t : n;
}
function Ms(e, t) {
	if (!e) return [];
	let n = e.aenderung?.zeit ? t("aenderungWert", {
		zeit: e.aenderung.zeit,
		quelle: e.aenderung.quelle
	}) : t("aenderungKeine"), r = [
		{
			label: t("ziel"),
			wert: e.ziel || t("unbekannt")
		},
		{
			label: t("sollQuelle"),
			wert: e.soll_quelle
		},
		...e.auth_art ? [{
			label: t("anmeldung"),
			wert: e.auth_art
		}] : [],
		{
			label: t("profilVersion"),
			wert: String(e.profil_version)
		},
		{
			label: t("aenderung"),
			wert: n
		},
		{
			label: t("image"),
			wert: js(e.image_vorhanden, t("vorhanden"), t("fehlt"), t)
		},
		{
			label: t("netzsperre"),
			wert: js(e.netzsperre_aktiv, t("aktiv"), t("inaktiv"), t)
		},
		{
			label: t("kontingent"),
			wert: e.github_rest_kontingent === null ? t("unbekannt") : String(e.github_rest_kontingent)
		}
	];
	return e.runner_version && r.push({
		label: t("runnerVersion"),
		wert: e.runner_frist ? t("runnerVersionFrist", {
			version: e.runner_version,
			frist: e.runner_frist
		}) : e.runner_version
	}), r;
}
var Ns = (e) => e == null ? "–" : String(e);
function Ps(e) {
	return e ? Object.entries(e.klassen).sort(([e], [t]) => e.localeCompare(t)).map(([e, t]) => ({
		name: e,
		aktiv: t.aktiv,
		soll: Ns(t.soll),
		max: Ns(t.max),
		instanzen: Ns(t.instanzen_aktiv),
		registriert: Ns(t.registriert),
		belegt: Ns(t.belegt),
		warteschlange: Ns(t.warteschlange),
		gruende: t.gruende.join("; ")
	})) : [];
}
function Fs(e) {
	return !!(e && Object.values(e.klassen).some((e) => typeof e.warteschlange == "number"));
}
function Is(e) {
	if (e == null) return "–";
	if (Array.isArray(e)) {
		let t = e.map((e) => String(typeof e == "object" && e ? e.name ?? "" : e)).filter(Boolean);
		return t.length ? t.join(", ") : String(e.length);
	}
	return typeof e == "object" ? JSON.stringify(e) : String(e);
}
function Ls(e) {
	return e ? Object.entries(e).sort(([e], [t]) => e.localeCompare(t)).map(([e, t]) => ({
		label: e,
		wert: Is(t)
	})) : [];
}
var Rs = [
	["statisch", "oStatisch"],
	["lokal", "oLokal"],
	["datei", "oDatei"]
], zs = [
	{
		pfad: ["soll_quelle", "art"],
		key: "fSollQuelle",
		art: "auswahl",
		optionen: (e) => Rs.map(([t, n]) => ({
			wert: t,
			label: e(n)
		}))
	},
	{
		pfad: ["soll_quelle", "datei"],
		key: "fSollDatei",
		art: "text"
	},
	{
		pfad: ["backend"],
		key: "fBackend",
		art: "text"
	},
	{
		pfad: ["image"],
		key: "fImage",
		art: "text"
	},
	{
		pfad: ["reserve", "cpus"],
		key: "fReserveCpus",
		art: "zahl"
	},
	{
		pfad: ["reserve", "speicher_gb"],
		key: "fReserveSpeicher",
		art: "zahl"
	}
], Bs = [
	{
		pfad: ["skalierung", "vorrang_interaktiv"],
		key: "fVorrang",
		art: "schalter"
	},
	{
		pfad: ["skalierung", "leerlauf_minuten"],
		key: "fLeerlauf",
		art: "zahl"
	},
	{
		pfad: ["skalierung", "anteil_bei_nutzung"],
		key: "fAnteil",
		art: "zahl",
		schritt: "0.05"
	},
	{
		pfad: ["skalierung", "swap_sperre_gb"],
		key: "fSwap",
		art: "zahl",
		schritt: "0.5"
	},
	{
		pfad: ["skalierung", "ram_frei_min_gb"],
		key: "fRam",
		art: "zahl",
		schritt: "0.5"
	},
	{
		pfad: ["skalierung", "last_je_kern_max"],
		key: "fLast",
		art: "zahl",
		schritt: "0.05"
	},
	{
		pfad: ["skalierung", "temperatur_max_c"],
		key: "fTemperatur",
		art: "zahl"
	},
	{
		pfad: ["skalierung", "volllast_von"],
		key: "fVon",
		art: "zahl"
	},
	{
		pfad: ["skalierung", "volllast_bis"],
		key: "fBis",
		art: "zahl"
	},
	{
		pfad: ["skalierung", "haltezeit_s"],
		key: "fHaltezeit",
		art: "zahl"
	}
], Vs = [{
	pfad: [
		"skalierung",
		"thermik",
		"aktiv"
	],
	key: "fThermikAktiv",
	art: "schalter"
}, {
	pfad: [
		"skalierung",
		"thermik",
		"url"
	],
	key: "fThermikUrl",
	art: "text"
}], Hs = [{
	pfad: ["netz", "aktiv"],
	key: "fNetzAktiv",
	art: "schalter"
}, {
	pfad: ["netz", "sperre_pflicht"],
	key: "fSperre",
	art: "schalter"
}], Us = [
	{
		feld: "art",
		key: "kArt",
		art: "auswahl",
		optionen: (e) => [{
			wert: "cpu",
			label: e("oCpu")
		}, {
			wert: "gpu",
			label: e("oGpu")
		}]
	},
	{
		feld: "aktiv",
		key: "kAktiv",
		art: "schalter"
	},
	{
		feld: "min_instanzen",
		key: "kMin",
		art: "zahl"
	},
	{
		feld: "max_instanzen",
		key: "kMax",
		art: "zahl"
	},
	{
		feld: "leise_max",
		key: "kLeise",
		art: "zahl"
	},
	{
		feld: "cpus",
		key: "kCpus",
		art: "zahl"
	},
	{
		feld: "speicher_gb",
		key: "kSpeicher",
		art: "zahl"
	},
	{
		feld: "vram_mb",
		key: "kVram",
		art: "zahl"
	},
	{
		feld: "labels",
		key: "kLabels",
		art: "liste"
	}
];
function Ws(e, t) {
	return t === "liste" ? Array.isArray(e) ? e.map(String).join(", ") : "" : e == null ? "" : String(e);
}
function Gs(e, t, { t: n, fehler: r, eingaben: i }) {
	let a = Ko(e, t.pfad);
	if (a === void 0) return null;
	let o = t.pfad.join(".");
	return {
		id: o,
		pfad: t.pfad,
		label: n(t.key),
		art: t.art,
		wert: i[o] ?? Ws(a, t.art),
		an: a === !0,
		optionen: t.optionen?.(n) ?? [],
		schritt: t.schritt ?? "1",
		fehler: r.get(o) ?? ""
	};
}
function Ks(e, t, n, r, i) {
	let a = r.map((e) => Gs(n, e, i)).filter((e) => e !== null);
	return a.length ? {
		id: e,
		titel: t,
		felder: a
	} : null;
}
function qs(e) {
	return e.replace(/\[(\d+)\]/g, ".$1");
}
function Js(e) {
	return e.pruefung?.probleme ?? e.stand?.probleme ?? [];
}
function Ys(e, t) {
	return t === "ungueltig" ? e("klasseNameUngueltig") : t === "vergeben" ? e("klasseNameVergeben") : "";
}
function Xs(e, t, n, r) {
	let i = as(t, n) === "gpu", a = Us.filter((e) => i || e.feld !== "vram_mb").map(({ feld: e, ...t }) => ({
		...t,
		pfad: [
			"klassen",
			n,
			e
		]
	})), o = Ks(`klasse-${n}`, r.t("abschnittKlasse", { name: n }), t, a, r);
	if (!o) return null;
	let s = e.klassenNamen[n] ?? n, c = s === n ? "" : Ys(r.t, os(t, s.trim(), n));
	return {
		...o,
		klasse: {
			alt: n,
			wert: s,
			fehler: c,
			geaendert: s.trim() !== n && !c
		}
	};
}
function Zs(e, t) {
	let n = e.entwurf;
	if (!n) return [];
	let r = {
		t,
		fehler: new Map(Js(e).map((e) => [qs(e.feld), e.meldung])),
		eingaben: e.eingaben
	}, i = is(n), a = i.filter((e) => as(n, e) === "gpu"), o = [
		Ks("allgemein", t("abschnittAllgemein"), n, zs, r),
		Ks("regelung", t("abschnittRegelung"), n, Bs, r),
		Ks("thermik", t("abschnittThermik"), n, Vs, r),
		Ks("netz", t("abschnittNetz"), n, Hs, r),
		...i.map((t) => Xs(e, n, t, r))
	], s = Ko(n, ["gpus"]);
	if (Array.isArray(s) && a.length) {
		let e = () => a.map((e) => ({
			wert: e,
			label: e
		}));
		s.forEach((i, a) => {
			let s = String(typeof i == "object" && i ? i.name ?? a : a);
			o.push(Ks(`karte-${a}`, t("abschnittKarte", {
				index: a,
				name: s
			}), n, [{
				pfad: [
					"gpus",
					a,
					"erlaubt"
				],
				key: "gErlaubt",
				art: "schalter"
			}, {
				pfad: [
					"gpus",
					a,
					"klasse"
				],
				key: "gKlasse",
				art: "auswahl",
				optionen: e
			}], r));
		});
	}
	return o.filter((e) => e !== null);
}
function Qs(e, t) {
	let n = e.neueKlasse.trim(), r = n ? Ys(t, os(e.entwurf, n)) : "";
	return {
		wert: e.neueKlasse,
		fehler: r,
		moeglich: !!n && !r
	};
}
function $s(e) {
	let t = e.pruefung;
	return t ? {
		gueltig: t.gueltig,
		aenderungen: t.aenderungen,
		schritte: t.schritte,
		rootBefehl: t.netzsperre_befehl ?? ""
	} : null;
}
function ec(e, t) {
	let n = new Map((e.werkzeuge?.werkzeuge ?? []).map((e) => [e.name, e])), r = e.werkzeugEntwurf ?? {};
	return Object.keys(r).sort().map((i) => ({
		profil: i,
		titel: t("werkzeugProfil", { name: i }),
		zeilen: Object.entries(r[i] ?? {}).sort(([e], [t]) => e.localeCompare(t)).map(([r, a]) => ({
			id: `${i}-${r}`,
			werkzeug: r,
			bereich: n.get(r)?.bereich ?? "",
			imImage: n.get(r)?.im_image || t("nichtInstalliert"),
			aktiv: a.aktiv,
			zeitlimit: e.eingaben[us(i, r, "zeitlimit_s")] ?? String(a.zeitlimit_s),
			prioritaet: e.eingaben[us(i, r, "prioritaet")] ?? String(a.prioritaet)
		}))
	}));
}
function tc(e) {
	return JSON.stringify(e.werkzeugEntwurf) !== JSON.stringify(e.werkzeuge?.profile ?? null);
}
function nc(e, t) {
	let n = $o(e.entwurf);
	return n.map((e, r) => ({
		...e,
		index: r,
		rangText: t("rang", { rang: e.rang }),
		hoch: t("hoch", { name: e.klasse }),
		runter: t("runter", { name: e.klasse }),
		ersteZeile: r === 0,
		letzteZeile: r === n.length - 1
	}));
}
function rc(e, t) {
	let n = $o(e.entwurf);
	if (!n.length) return "";
	let r = ns(n);
	return r ? t("weichtZuerst", { name: r.klasse }) : t("keinerVerdraengbar");
}
//#endregion
//#region src/composables/useId.ts
var ic = 0;
function ac(e = "fa") {
	return ic += 1, `${e}-${ic}`;
}
//#endregion
//#region src/composables/useStore.ts
function oc(e) {
	let t = /* @__PURE__ */ Zt(e.get()), n = e.subscribe(() => {
		t.value = e.get();
	});
	return je() && Me(n), t;
}
//#endregion
//#region src/i18n/i18n.ts
var sc = Symbol("flowaudit-locale"), cc = /* @__PURE__ */ Xt(xo());
So(() => {
	cc.value = xo();
});
function lc() {
	return Pn(sc, cc);
}
function uc(e, t) {
	let n = lc(), r = $(() => t?.() ?? n.value);
	return {
		locale: r,
		t: (t, n) => vo(e, r.value, t, n)
	};
}
//#endregion
//#region src/base/FaBadge.vue
var dc = /* @__PURE__ */ z({
	__name: "FaBadge",
	props: {
		tone: { default: "neutral" },
		label: { default: "" }
	},
	setup(e) {
		return (t, n) => (G(), K("span", { class: ve(["fa-badge", `fa-badge--${e.tone}`]) }, [_r(t.$slots, "default", {}, () => [X(O(e.label), 1)])], 2));
	}
}), fc = [
	"width",
	"height",
	"role",
	"aria-label",
	"aria-hidden"
], pc = ["d"], mc = /* @__PURE__ */ z({
	__name: "FaIcon",
	props: {
		name: {},
		size: { default: 18 },
		label: { default: "" }
	},
	setup(e) {
		let t = e, n = $(() => Do[t.name]), r = $(() => typeof t.size == "number" ? `${t.size}px` : t.size);
		return (t, i) => (G(), K("svg", {
			class: "fa-icon",
			viewBox: "0 0 24 24",
			width: r.value,
			height: r.value,
			fill: "none",
			stroke: "currentColor",
			"stroke-linecap": "round",
			"stroke-linejoin": "round",
			role: e.label ? "img" : void 0,
			"aria-label": e.label || void 0,
			"aria-hidden": e.label ? void 0 : "true",
			focusable: "false"
		}, [(G(!0), K(U, null, B(n.value, (e, t) => (G(), K("path", {
			key: t,
			d: e
		}, null, 8, pc))), 128))], 8, fc));
	}
}), hc = [
	"type",
	"disabled",
	"aria-busy",
	"aria-pressed",
	"aria-label",
	"title"
], gc = {
	key: 1,
	class: "fa-button__label"
}, _c = /* @__PURE__ */ z({
	__name: "FaButton",
	props: {
		variant: { default: "secondary" },
		size: { default: "md" },
		icon: { default: void 0 },
		iconOnly: {
			type: Boolean,
			default: !1
		},
		label: { default: "" },
		type: { default: "button" },
		disabled: {
			type: Boolean,
			default: !1
		},
		loading: {
			type: Boolean,
			default: !1
		},
		pressed: {
			type: Boolean,
			default: void 0
		}
	},
	emits: ["click"],
	setup(e) {
		let t = e, n = $(() => [
			"fa-button",
			`fa-button--${t.variant}`,
			`fa-button--${t.size}`,
			{
				"fa-button--icon-only": t.iconOnly,
				"fa-button--loading": t.loading
			}
		]);
		return (t, r) => (G(), K("button", {
			class: ve(n.value),
			type: e.type,
			disabled: e.disabled || e.loading,
			"aria-busy": e.loading || void 0,
			"aria-pressed": e.pressed,
			"aria-label": e.iconOnly ? e.label : void 0,
			title: e.iconOnly ? e.label : void 0,
			onClick: r[0] ||= (e) => t.$emit("click", e)
		}, [e.icon ? (G(), q(mc, {
			key: 0,
			name: e.icon,
			size: e.size === "sm" ? 14 : 16
		}, null, 8, ["name", "size"])) : Z("", !0), e.iconOnly ? Z("", !0) : (G(), K("span", gc, [_r(t.$slots, "default", {}, () => [X(O(e.label), 1)])]))], 10, hc));
	}
}), vc = { class: "fa-runner__feld fa-runner__klassenname" }, yc = { class: "fa-runner__aktionen" }, bc = [
	"value",
	"disabled",
	"aria-invalid",
	"aria-describedby"
], xc = ["id"], Sc = /* @__PURE__ */ z({
	__name: "RunnerClassName",
	props: {
		klasse: {},
		controller: {},
		t: { type: Function },
		uid: {},
		nurLesen: { type: Boolean }
	},
	setup(e) {
		let t = e, n = `${t.uid}-klasse-${t.klasse.alt}-name`;
		function r(e) {
			t.controller.klassenNameEingabe(t.klasse.alt, e.target.value);
		}
		return (t, i) => (G(), K("div", vc, [
			J("label", { for: n }, O(e.t("klasseName")), 1),
			J("span", yc, [J("input", {
				id: n,
				class: "fa-runner__eingabe",
				type: "text",
				maxlength: "31",
				value: e.klasse.wert,
				disabled: e.nurLesen,
				"aria-invalid": e.klasse.fehler ? "true" : void 0,
				"aria-describedby": e.klasse.fehler ? `${n}-fehler` : void 0,
				onInput: r
			}, null, 40, bc), Y(_c, {
				size: "sm",
				disabled: e.nurLesen || !e.klasse.geaendert,
				onClick: i[0] ||= (t) => e.controller.klasseUmbenennen(e.klasse.alt)
			}, {
				default: R(() => [X(O(e.t("umbenennen")), 1)]),
				_: 1
			}, 8, ["disabled"])]),
			e.klasse.fehler ? (G(), K("p", {
				key: 0,
				id: `${n}-fehler`,
				class: "fa-runner__feldfehler"
			}, O(e.klasse.fehler), 9, xc)) : Z("", !0)
		]));
	}
}), Cc = { class: "fa-runner__abschnitt" }, wc = { class: "fa-runner__feld fa-runner__klassenname" }, Tc = { class: "fa-runner__aktionen" }, Ec = [
	"value",
	"disabled",
	"aria-invalid",
	"aria-describedby"
], Dc = ["id"], Oc = /* @__PURE__ */ z({
	__name: "RunnerNewClass",
	props: {
		state: {},
		controller: {},
		t: { type: Function },
		uid: {}
	},
	setup(e) {
		let t = e, n = $(() => Qs(t.state, t.t)), r = $(() => Ds(t.state)), i = `${t.uid}-neue-klasse`;
		return (t, a) => (G(), K("fieldset", Cc, [J("legend", null, O(e.t("neueKlasse")), 1), J("div", wc, [
			J("label", { for: i }, O(e.t("klasseName")), 1),
			J("span", Tc, [J("input", {
				id: i,
				class: "fa-runner__eingabe",
				type: "text",
				maxlength: "31",
				value: n.value.wert,
				disabled: r.value,
				"aria-invalid": n.value.fehler ? "true" : void 0,
				"aria-describedby": n.value.fehler ? `${i}-fehler` : void 0,
				onInput: a[0] ||= (t) => e.controller.neueKlasseEingabe(t.target.value)
			}, null, 40, Ec), Y(_c, {
				size: "sm",
				icon: "plus",
				disabled: r.value || !n.value.moeglich,
				onClick: a[1] ||= (t) => e.controller.klasseHinzufuegen()
			}, {
				default: R(() => [X(O(e.t("hinzufuegen")), 1)]),
				_: 1
			}, 8, ["disabled"])]),
			n.value.fehler ? (G(), K("p", {
				key: 0,
				id: `${i}-fehler`,
				class: "fa-runner__feldfehler"
			}, O(n.value.fehler), 9, Dc)) : Z("", !0)
		])]));
	}
}), kc = [
	"id",
	"checked",
	"disabled",
	"aria-invalid",
	"aria-describedby",
	"onChange"
], Ac = ["for"], jc = ["for"], Mc = [
	"id",
	"value",
	"disabled",
	"aria-invalid",
	"aria-describedby",
	"onChange"
], Nc = ["value"], Pc = [
	"id",
	"type",
	"step",
	"value",
	"disabled",
	"aria-invalid",
	"aria-describedby",
	"onInput"
], Fc = ["id"], Ic = /* @__PURE__ */ z({
	__name: "RunnerFields",
	props: {
		state: {},
		controller: {},
		t: { type: Function },
		uid: {}
	},
	setup(e) {
		let t = e, n = $(() => Zs(t.state, t.t)), r = $(() => Ds(t.state));
		function i(e, n) {
			let r = n.target;
			t.controller.eingabe(e.pfad, e.art, e.art === "schalter" ? r.checked : r.value);
		}
		return (t, a) => (G(), K(U, null, [(G(!0), K(U, null, B(n.value, (t) => (G(), K("fieldset", {
			key: t.id,
			class: "fa-runner__abschnitt"
		}, [
			J("legend", null, O(t.titel), 1),
			t.klasse ? (G(), q(Sc, {
				key: 0,
				klasse: t.klasse,
				controller: e.controller,
				t: e.t,
				uid: e.uid,
				"nur-lesen": r.value
			}, null, 8, [
				"klasse",
				"controller",
				"t",
				"uid",
				"nur-lesen"
			])) : Z("", !0),
			(G(!0), K(U, null, B(t.felder, (t) => (G(), K("div", {
				key: t.id,
				class: ve(["fa-runner__feld", t.art === "schalter" && "fa-runner__feld--schalter"])
			}, [t.art === "schalter" ? (G(), K(U, { key: 0 }, [J("input", {
				id: `${e.uid}-${t.id}`,
				type: "checkbox",
				checked: t.an,
				disabled: r.value,
				"aria-invalid": t.fehler ? "true" : void 0,
				"aria-describedby": t.fehler ? `${e.uid}-${t.id}-fehler` : void 0,
				onChange: (e) => i(t, e)
			}, null, 40, kc), J("label", { for: `${e.uid}-${t.id}` }, O(t.label), 9, Ac)], 64)) : (G(), K(U, { key: 1 }, [J("label", { for: `${e.uid}-${t.id}` }, O(t.label), 9, jc), t.art === "auswahl" ? (G(), K("select", {
				key: 0,
				id: `${e.uid}-${t.id}`,
				class: "fa-runner__eingabe",
				value: t.wert,
				disabled: r.value,
				"aria-invalid": t.fehler ? "true" : void 0,
				"aria-describedby": t.fehler ? `${e.uid}-${t.id}-fehler` : void 0,
				onChange: (e) => i(t, e)
			}, [(G(!0), K(U, null, B(t.optionen, (e) => (G(), K("option", {
				key: e.wert,
				value: e.wert
			}, O(e.label), 9, Nc))), 128))], 40, Mc)) : (G(), K("input", {
				key: 1,
				id: `${e.uid}-${t.id}`,
				class: "fa-runner__eingabe",
				type: t.art === "zahl" ? "number" : "text",
				step: t.art === "zahl" ? t.schritt : void 0,
				value: t.wert,
				disabled: r.value,
				"aria-invalid": t.fehler ? "true" : void 0,
				"aria-describedby": t.fehler ? `${e.uid}-${t.id}-fehler` : void 0,
				onInput: (e) => i(t, e)
			}, null, 40, Pc))], 64)), t.fehler ? (G(), K("p", {
				key: 2,
				id: `${e.uid}-${t.id}-fehler`,
				class: "fa-runner__feldfehler"
			}, O(t.fehler), 9, Fc)) : Z("", !0)], 2))), 128))
		]))), 128)), Y(Oc, {
			state: e.state,
			controller: e.controller,
			t: e.t,
			uid: e.uid
		}, null, 8, [
			"state",
			"controller",
			"t",
			"uid"
		])], 64));
	}
}), Lc = { class: "fa-runner__muted" }, Rc = {
	key: 0,
	class: "fa-runner__muted"
}, zc = {
	key: 1,
	class: "fa-runner__prioritaeten"
}, Bc = { class: "fa-runner__rang" }, Vc = { class: "fa-runner__klasse" }, Hc = { class: "fa-runner__feld fa-runner__feld--schalter" }, Uc = [
	"id",
	"checked",
	"disabled",
	"onChange"
], Wc = ["for"], Gc = { class: "fa-runner__feld fa-runner__feld--schalter" }, Kc = ["for"], qc = [
	"id",
	"value",
	"disabled",
	"onInput"
], Jc = {
	key: 2,
	class: "fa-runner__muted"
}, Yc = /* @__PURE__ */ z({
	__name: "RunnerPriorityList",
	props: {
		state: {},
		controller: {},
		t: { type: Function },
		uid: {}
	},
	setup(e) {
		let t = e, n = $(() => nc(t.state, t.t)), r = $(() => rc(t.state, t.t)), i = $(() => Ds(t.state));
		function a(e, n) {
			t.controller.prioritaet(e, { verdraengbar: n.target.checked });
		}
		function o(e, n) {
			t.controller.prioritaet(e, { min: Number(n.target.value) || 0 });
		}
		return (t, s) => (G(), K(U, null, [
			J("p", Lc, O(e.t("prioritaetenHinweis")), 1),
			n.value.length ? (G(), K("ol", zc, [(G(!0), K(U, null, B(n.value, (t) => (G(), K("li", {
				key: t.klasse,
				class: "fa-runner__prioritaet"
			}, [
				J("span", Bc, O(t.rangText), 1),
				J("strong", Vc, O(t.klasse), 1),
				Y(_c, {
					size: "sm",
					icon: "chevron-up",
					"icon-only": "",
					label: t.hoch,
					disabled: i.value || t.ersteZeile,
					onClick: (n) => e.controller.verschiebe(t.index, -1)
				}, null, 8, [
					"label",
					"disabled",
					"onClick"
				]),
				Y(_c, {
					size: "sm",
					icon: "chevron-down",
					"icon-only": "",
					label: t.runter,
					disabled: i.value || t.letzteZeile,
					onClick: (n) => e.controller.verschiebe(t.index, 1)
				}, null, 8, [
					"label",
					"disabled",
					"onClick"
				]),
				J("span", Hc, [J("input", {
					id: `${e.uid}-prio-${t.index}-verdraengbar`,
					type: "checkbox",
					checked: t.verdraengbar,
					disabled: i.value,
					onChange: (e) => a(t.index, e)
				}, null, 40, Uc), J("label", { for: `${e.uid}-prio-${t.index}-verdraengbar` }, O(e.t("verdraengbar")), 9, Wc)]),
				J("span", Gc, [J("label", { for: `${e.uid}-prio-${t.index}-min` }, O(e.t("mindestens")), 9, Kc), J("input", {
					id: `${e.uid}-prio-${t.index}-min`,
					class: "fa-runner__eingabe fa-runner__schmal",
					type: "number",
					min: "0",
					value: String(t.min),
					disabled: i.value,
					onInput: (e) => o(t.index, e)
				}, null, 40, qc)])
			]))), 128))])) : (G(), K("p", Rc, O(e.t("keinePrioritaeten")), 1)),
			r.value ? (G(), K("p", Jc, O(r.value), 1)) : Z("", !0)
		], 64));
	}
}), Xc = {
	key: 0,
	class: "fa-runner__konflikt",
	role: "alert"
}, Zc = { class: "fa-runner__tabelle" }, Qc = { scope: "col" }, $c = { scope: "col" }, el = { scope: "col" }, tl = { scope: "row" }, nl = { class: "fa-runner__aktionen" }, rl = ["aria-label"], il = { class: "fa-runner__zwischen" }, al = {
	key: 0,
	class: "fa-runner__muted"
}, ol = { class: "fa-runner__zwischen" }, sl = { class: "fa-runner__schritte" }, cl = { class: "fa-runner__muted" }, ll = { class: "fa-runner__befehl" }, ul = /* @__PURE__ */ z({
	__name: "RunnerReview",
	props: {
		state: {},
		controller: {},
		t: { type: Function }
	},
	setup(e) {
		let t = e, n = $(() => $s(t.state)), r = $(() => String(Ko(t.state.konflikt?.gespeichert.profil, ["aenderung", "quelle"]) ?? "–"));
		return (t, i) => (G(), K(U, null, [e.state.konflikt ? (G(), K("section", Xc, [
			J("p", null, O(e.t("konflikt", { meldung: e.state.konflikt.meldung })), 1),
			J("table", Zc, [J("thead", null, [J("tr", null, [
				J("th", Qc, O(e.t("konfliktFeld")), 1),
				J("th", $c, O(e.t("konfliktEntwurf")), 1),
				J("th", el, O(e.t("konfliktGespeichert", { quelle: r.value })), 1)
			])]), J("tbody", null, [(G(!0), K(U, null, B(e.state.konflikt.unterschiede, (e) => (G(), K("tr", { key: e.pfad }, [
				J("th", tl, [J("code", null, O(e.pfad), 1)]),
				J("td", null, [J("code", null, O(e.entwurf), 1)]),
				J("td", null, [J("code", null, O(e.gespeichert), 1)])
			]))), 128))])]),
			J("div", nl, [Y(_c, { onClick: i[0] ||= (t) => e.controller.gespeichertUebernehmen() }, {
				default: R(() => [X(O(e.t("gespeichertUebernehmen")), 1)]),
				_: 1
			}), Y(_c, {
				variant: "primary",
				onClick: i[1] ||= (t) => e.controller.entwurfTrotzdemAnwenden()
			}, {
				default: R(() => [X(O(e.t("entwurfAnwenden")), 1)]),
				_: 1
			})])
		])) : Z("", !0), n.value ? (G(), K("section", {
			key: 1,
			class: "fa-runner__vorschau",
			"aria-label": e.t("vorschau")
		}, [
			J("h3", il, [X(O(e.t("vorschau")) + " ", 1), Y(dc, { tone: n.value.gueltig ? "success" : "danger" }, {
				default: R(() => [X(O(n.value.gueltig ? e.t("gueltig") : e.t("ungueltig")), 1)]),
				_: 1
			}, 8, ["tone"])]),
			n.value.aenderungen.length ? Z("", !0) : (G(), K("p", al, O(e.t("keineAenderung")), 1)),
			(G(!0), K(U, null, B(n.value.aenderungen, (e) => (G(), K("details", {
				key: e.datei,
				class: "fa-runner__diff"
			}, [J("summary", null, O(e.datei), 1), J("pre", null, O(e.diff), 1)]))), 128)),
			n.value.schritte.length ? (G(), K(U, { key: 1 }, [J("h4", ol, O(e.t("schritte")), 1), J("ol", sl, [(G(!0), K(U, null, B(n.value.schritte, (e) => (G(), K("li", { key: e }, O(e), 1))), 128))])], 64)) : Z("", !0),
			n.value.rootBefehl ? (G(), K(U, { key: 2 }, [J("p", cl, O(e.t("rootBefehl")), 1), J("pre", ll, [J("code", null, O(n.value.rootBefehl), 1)])], 64)) : Z("", !0)
		], 8, rl)) : Z("", !0)], 64));
	}
}), dl = ["aria-label"], fl = { class: "fa-runner__aktionen" }, pl = /* @__PURE__ */ z({
	__name: "RunnerProfileForm",
	props: {
		state: {},
		controller: {},
		t: { type: Function },
		uid: {}
	},
	setup(e) {
		let t = e, n = $(() => Js(t.state)), r = $(() => Ds(t.state)), i = $(() => Os(t.state));
		return (t, a) => (G(), K("form", {
			class: "fa-runner__formular",
			novalidate: "",
			onSubmit: a[2] ||= oo((t) => e.controller.pruefen(), ["prevent"])
		}, [
			n.value.length ? (G(), K("ul", {
				key: 0,
				class: "fa-runner__probleme",
				"aria-label": e.t("probleme")
			}, [(G(!0), K(U, null, B(n.value, (e) => (G(), K("li", { key: `${e.feld}-${e.meldung}` }, O(e.feld) + ": " + O(e.meldung), 1))), 128))], 8, dl)) : Z("", !0),
			e.state.ansicht === "einstellungen" ? (G(), q(Ic, {
				key: 1,
				state: e.state,
				controller: e.controller,
				t: e.t,
				uid: e.uid
			}, null, 8, [
				"state",
				"controller",
				"t",
				"uid"
			])) : (G(), q(Yc, {
				key: 2,
				state: e.state,
				controller: e.controller,
				t: e.t,
				uid: e.uid
			}, null, 8, [
				"state",
				"controller",
				"t",
				"uid"
			])),
			J("div", fl, [
				Y(_c, {
					type: "submit",
					disabled: r.value,
					loading: e.state.busy === "pruefen"
				}, {
					default: R(() => [X(O(e.t("pruefen")), 1)]),
					_: 1
				}, 8, ["disabled", "loading"]),
				Y(_c, {
					variant: "primary",
					disabled: r.value || !i.value,
					loading: e.state.busy === "anwenden",
					onClick: a[0] ||= (t) => e.controller.anwenden()
				}, {
					default: R(() => [X(O(e.t("anwenden")), 1)]),
					_: 1
				}, 8, ["disabled", "loading"]),
				Y(_c, {
					disabled: !i.value,
					onClick: a[1] ||= (t) => e.controller.verwerfen()
				}, {
					default: R(() => [X(O(e.t("verwerfen")), 1)]),
					_: 1
				}, 8, ["disabled"]),
				i.value ? (G(), q(dc, {
					key: 0,
					tone: "warning"
				}, {
					default: R(() => [X(O(e.t("ungespeichert")), 1)]),
					_: 1
				})) : Z("", !0)
			]),
			Y(ul, {
				state: e.state,
				controller: e.controller,
				t: e.t
			}, null, 8, [
				"state",
				"controller",
				"t"
			])
		], 32));
	}
}), ml = { class: "fa-runner__zwischen" }, hl = { class: "fa-runner__daten" }, gl = {
	key: 0,
	class: "fa-runner__tabelle"
}, _l = { scope: "col" }, vl = { scope: "col" }, yl = { scope: "col" }, bl = { scope: "col" }, xl = { scope: "col" }, Sl = { scope: "col" }, Cl = {
	key: 0,
	scope: "col"
}, wl = { scope: "col" }, Tl = { scope: "row" }, El = { key: 0 }, Dl = {
	key: 1,
	class: "fa-runner__muted"
}, Ol = { class: "fa-runner__zwischen" }, kl = { class: "fa-runner__daten" }, Al = { class: "fa-runner__aktionen" }, jl = /* @__PURE__ */ z({
	__name: "RunnerStatusPanel",
	props: {
		state: {},
		controller: {},
		t: { type: Function }
	},
	setup(e) {
		let t = e, n = $(() => Ms(t.state.status, t.t)), r = $(() => Ps(t.state.status)), i = $(() => Fs(t.state.status)), a = $(() => Ls(t.state.status?.hardware));
		return (t, o) => (G(), K(U, null, [e.state.status ? (G(), K(U, { key: 0 }, [
			J("h3", ml, O(e.t("ueberblick")), 1),
			J("dl", hl, [(G(!0), K(U, null, B(n.value, (e) => (G(), K("div", {
				key: e.label,
				class: "fa-runner__datum"
			}, [J("dt", null, O(e.label), 1), J("dd", null, O(e.wert), 1)]))), 128))]),
			r.value.length ? (G(), K("table", gl, [
				J("caption", null, O(e.t("klassen")), 1),
				J("thead", null, [J("tr", null, [
					J("th", _l, O(e.t("spalteKlasse")), 1),
					J("th", vl, O(e.t("spalteSoll")), 1),
					J("th", yl, O(e.t("spalteMax")), 1),
					J("th", bl, O(e.t("spalteInstanzen")), 1),
					J("th", xl, O(e.t("spalteRegistriert")), 1),
					J("th", Sl, O(e.t("spalteBelegt")), 1),
					i.value ? (G(), K("th", Cl, O(e.t("spalteWarteschlange")), 1)) : Z("", !0),
					J("th", wl, O(e.t("spalteGruende")), 1)
				])]),
				J("tbody", null, [(G(!0), K(U, null, B(r.value, (t) => (G(), K("tr", { key: t.name }, [
					J("th", Tl, [X(O(t.name) + " ", 1), t.aktiv ? Z("", !0) : (G(), q(dc, { key: 0 }, {
						default: R(() => [X(O(e.t("inaktiv")), 1)]),
						_: 1
					}))]),
					J("td", null, O(t.soll), 1),
					J("td", null, O(t.max), 1),
					J("td", null, O(t.instanzen), 1),
					J("td", null, O(t.registriert), 1),
					J("td", null, O(t.belegt), 1),
					i.value ? (G(), K("td", El, O(t.warteschlange), 1)) : Z("", !0),
					J("td", null, O(t.gruende), 1)
				]))), 128))])
			])) : (G(), K("p", Dl, O(e.t("keineKlassen")), 1)),
			J("h3", Ol, O(e.t("hardware")), 1),
			J("dl", kl, [(G(!0), K(U, null, B(a.value, (e) => (G(), K("div", {
				key: e.label,
				class: "fa-runner__datum"
			}, [J("dt", null, O(e.label), 1), J("dd", null, O(e.wert), 1)]))), 128))])
		], 64)) : Z("", !0), J("div", Al, [Y(_c, {
			icon: "clock",
			loading: e.state.busy === "load",
			onClick: o[0] ||= (t) => e.controller.load()
		}, {
			default: R(() => [X(O(e.t("refresh")), 1)]),
			_: 1
		}, 8, ["loading"])])], 64));
	}
}), Ml = {
	key: 0,
	class: "fa-runner__muted"
}, Nl = { scope: "col" }, Pl = { scope: "col" }, Fl = { scope: "col" }, Il = { scope: "col" }, Ll = { scope: "col" }, Rl = { scope: "col" }, zl = { scope: "row" }, Bl = [
	"checked",
	"disabled",
	"aria-label",
	"onChange"
], Vl = [
	"value",
	"disabled",
	"aria-label",
	"onInput"
], Hl = [
	"value",
	"disabled",
	"aria-label",
	"onInput"
], Ul = { class: "fa-runner__aktionen" }, Wl = /* @__PURE__ */ z({
	__name: "RunnerToolsPanel",
	props: {
		state: {},
		controller: {},
		t: { type: Function }
	},
	setup(e) {
		let t = e, n = $(() => ec(t.state, t.t)), r = $(() => Ds(t.state)), i = $(() => tc(t.state));
		function a(e, n, r) {
			t.controller.werkzeug(e, n, { aktiv: r.target.checked });
		}
		function o(e, n, r, i) {
			t.controller.werkzeugZahl(e, n, r, i.target.value);
		}
		return (t, s) => (G(), K(U, null, [
			n.value.length ? Z("", !0) : (G(), K("p", Ml, O(e.t("keineWerkzeuge")), 1)),
			(G(!0), K(U, null, B(n.value, (t) => (G(), K("table", {
				key: t.profil,
				class: "fa-runner__tabelle"
			}, [
				J("caption", null, O(t.titel), 1),
				J("thead", null, [J("tr", null, [
					J("th", Nl, O(e.t("spalteWerkzeug")), 1),
					J("th", Pl, O(e.t("spalteBereich")), 1),
					J("th", Fl, O(e.t("spalteImage")), 1),
					J("th", Il, O(e.t("spalteAktiv")), 1),
					J("th", Ll, O(e.t("spalteZeitlimit")), 1),
					J("th", Rl, O(e.t("spaltePrioritaet")), 1)
				])]),
				J("tbody", null, [(G(!0), K(U, null, B(t.zeilen, (n) => (G(), K("tr", { key: n.id }, [
					J("th", zl, O(n.werkzeug), 1),
					J("td", null, O(n.bereich), 1),
					J("td", null, O(n.imImage), 1),
					J("td", null, [J("input", {
						type: "checkbox",
						checked: n.aktiv,
						disabled: r.value,
						"aria-label": `${e.t("spalteAktiv")}: ${n.werkzeug}`,
						onChange: (e) => a(t.profil, n.werkzeug, e)
					}, null, 40, Bl)]),
					J("td", null, [J("input", {
						class: "fa-runner__eingabe fa-runner__schmal",
						type: "number",
						min: "1",
						value: n.zeitlimit,
						disabled: r.value,
						"aria-label": `${e.t("spalteZeitlimit")}: ${n.werkzeug}`,
						onInput: (e) => o(t.profil, n.werkzeug, "zeitlimit_s", e)
					}, null, 40, Vl)]),
					J("td", null, [J("input", {
						class: "fa-runner__eingabe fa-runner__schmal",
						type: "number",
						min: "0",
						value: n.prioritaet,
						disabled: r.value,
						"aria-label": `${e.t("spaltePrioritaet")}: ${n.werkzeug}`,
						onInput: (e) => o(t.profil, n.werkzeug, "prioritaet", e)
					}, null, 40, Hl)])
				]))), 128))])
			]))), 128)),
			J("div", Ul, [Y(_c, {
				variant: "primary",
				disabled: r.value || !i.value,
				loading: e.state.busy === "werkzeuge",
				onClick: s[0] ||= (t) => e.controller.werkzeugeSpeichern()
			}, {
				default: R(() => [X(O(e.t("speichern")), 1)]),
				_: 1
			}, 8, ["disabled", "loading"])])
		], 64));
	}
}), Gl = ["lang", "aria-label"], Kl = { class: "fa-runner__kopf" }, ql = { class: "fa-runner__titel" }, Jl = {
	key: 0,
	class: "fa-runner__meta"
}, Yl = ["aria-label"], Xl = [
	"id",
	"aria-selected",
	"aria-controls",
	"tabindex",
	"onClick"
], Zl = {
	key: 0,
	class: "fa-runner__muted",
	role: "status"
}, Ql = {
	key: 1,
	class: "fa-runner__failure",
	role: "alert"
}, $l = ["id", "aria-labelledby"], eu = {
	key: 0,
	class: "fa-runner__hinweise"
}, tu = {
	tag: "flowaudit-runner-console",
	component: /* @__PURE__ */ z({
		__name: "RunnerConsole",
		props: {
			port: { default: null },
			api: { default: "" },
			ansicht: { default: "status" },
			locale: { default: void 0 }
		},
		emits: ["applied", "error"],
		setup(e, { emit: t }) {
			let n = e, r = t, { t: i, locale: a } = uc(zo, () => n.locale), o = ac("fa-runner"), s = Cs({
				port: () => n.port,
				api: () => n.api,
				callbacks: () => ({
					applied: (e) => r("applied", e),
					failed: (e) => r("error", e)
				})
			});
			s.zeige(n.ansicht);
			let c = oc(s.store), l = $(() => Ts(c.value, i)), u = $(() => ks(c.value, i)), d = $(() => As(c.value, i));
			Ln(() => [n.port, n.api], () => void s.load(), { immediate: !0 });
			function f(e) {
				let t = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
				if (!t) return;
				e.preventDefault();
				let n = Es(c.value.ansicht, t);
				s.zeige(n), document.getElementById(`${o}-tab-${n}`)?.focus();
			}
			return (e, t) => (G(), K("section", {
				class: "fa-runner",
				lang: F(a),
				"aria-label": F(i)("title")
			}, [
				J("header", Kl, [J("h2", ql, O(F(i)("title")), 1), u.value ? (G(), K("p", Jl, O(u.value), 1)) : Z("", !0)]),
				J("div", {
					class: "fa-runner__reiter",
					role: "tablist",
					"aria-label": F(i)("tabs"),
					onKeydown: f
				}, [(G(!0), K(U, null, B(l.value, (e) => (G(), K("button", {
					id: `${F(o)}-tab-${e.id}`,
					key: e.id,
					type: "button",
					role: "tab",
					class: "fa-runner__tab",
					"aria-selected": e.selected ? "true" : "false",
					"aria-controls": `${F(o)}-panel`,
					tabindex: e.selected ? 0 : -1,
					onClick: (t) => F(s).zeige(e.id)
				}, O(e.label), 9, Xl))), 128))], 40, Yl),
				F(c).busy ? (G(), K("p", Zl, O(F(c).busy === "load" ? F(i)("loading") : F(i)("working")), 1)) : Z("", !0),
				F(c).error ? (G(), K("p", Ql, O(F(i)("failed", { message: F(c).error })), 1)) : Z("", !0),
				F(c).meldung ? (G(), K("p", {
					key: 2,
					class: ve(["fa-runner__meldung", `fa-runner__meldung--${F(c).meldung.ton}`]),
					role: "status"
				}, O(F(i)(F(c).meldung.key, F(c).meldung.params)), 3)) : Z("", !0),
				J("div", {
					id: `${F(o)}-panel`,
					class: "fa-runner__panel",
					role: "tabpanel",
					"aria-labelledby": `${F(o)}-tab-${F(c).ansicht}`,
					tabindex: "0"
				}, [d.value.length ? (G(), K("ul", eu, [(G(!0), K(U, null, B(d.value, (e) => (G(), K("li", {
					key: e.text,
					class: ve(["fa-runner__hinweis", `fa-runner__hinweis--${e.ton}`])
				}, O(e.text), 3))), 128))])) : Z("", !0), F(c).ansicht === "status" ? (G(), q(jl, {
					key: 1,
					state: F(c),
					controller: F(s),
					t: F(i)
				}, null, 8, [
					"state",
					"controller",
					"t"
				])) : F(c).ansicht === "werkzeuge" ? (G(), q(Wl, {
					key: 2,
					state: F(c),
					controller: F(s),
					t: F(i)
				}, null, 8, [
					"state",
					"controller",
					"t"
				])) : (G(), q(pl, {
					key: 3,
					state: F(c),
					controller: F(s),
					t: F(i),
					uid: F(o)
				}, null, 8, [
					"state",
					"controller",
					"t",
					"uid"
				]))], 8, $l)
			], 8, Gl));
		}
	})
}, nu = document.createElement("style");
nu.dataset.flowaudit = "runner", nu.textContent = e, document.head.append(nu), ho(tu);
//#endregion
