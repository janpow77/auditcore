"""Kommandozeile ``auditcore-documents`` (lesen, vergleichen, Einstellungen anlegen).

Ohne KI-Anbindung: Begründungsvorschläge sind Sache der Anwendung.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from auditcore_documents.compare import CompareOptions, compare_files
from auditcore_documents.errors import CompareError
from auditcore_documents.profiles import PROFILES, get_profile
from auditcore_documents.reading import read_document
from auditcore_documents.settings import load_settings, merge_settings, save_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="auditcore-documents",
        description="Vergleicht zwei DOCX-/DOCM-/PDF-Fassungen oder wendet Änderungsbefehle an.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    read = sub.add_parser("read", help="Vergleichseinheiten einer Datei als JSON ausgeben")
    read.add_argument("path", type=Path)
    read.add_argument("--mode", choices=["auto", "checklist", "text"], default="auto")

    compare = sub.add_parser("compare", help="zwei Fassungen vergleichen")
    compare.add_argument("old", type=Path)
    compare.add_argument("new", type=Path)
    compare.add_argument("-o", "--output", type=Path, help="DOCX-Ziel (Extra docx-render)")
    compare.add_argument("--json", type=Path, help="Ergebnis als JSON-Datei")
    compare.add_argument("--pdf", type=Path, help="Synopse als PDF (Extra pdf-render)")
    compare.add_argument("--config", type=Path, help="Einstellungsdatei (sonst Vorgaben)")
    compare.add_argument(
        "--profile", choices=sorted(PROFILES), default="auditcore.document_compare"
    )
    compare.add_argument("--mode", choices=["auto", "checklist", "text"])
    compare.add_argument("--comparison-type", choices=["standard", "article_law"])
    compare.add_argument("--threshold", type=int)
    compare.add_argument("--title")
    compare.add_argument("--user", default="")
    compare.add_argument("--header-text")
    compare.add_argument("--output-profile", choices=["memo", "text"])
    compare.add_argument("--include-editorial", action="store_true")

    create = sub.add_parser("create-config", help="Einstellungsdatei mit Vorgaben anlegen")
    create.add_argument("path", type=Path)
    return parser


def _compare(args: argparse.Namespace) -> dict[str, Any]:
    department = load_settings(args.config) if args.config else {}
    overrides = {
        key: value
        for key, value in {
            "mode": args.mode,
            "comparison_type": args.comparison_type,
            "threshold": args.threshold,
            "output_profile": args.output_profile,
            "include_editorial": args.include_editorial or None,
        }.items()
        if value is not None
    }
    effective, sources = merge_settings(department, {}, overrides)
    result = compare_files(
        args.old,
        args.new,
        profile=get_profile(args.profile),
        options=CompareOptions(
            mode=str(effective["mode"]),
            threshold=int(effective["threshold"]),
            include_answers=bool(effective["include_answers"]),
            include_notes=bool(effective["include_notes"]),
            include_editorial=bool(effective["include_editorial"]),
            highlight_words=bool(effective["highlight_words"]),
            output_sections=list(effective["output_sections"]),
            comparison_type=str(effective["comparison_type"]),
        ),
    )
    result.metadata["setting_sources"] = sources
    if args.output:
        from auditcore_documents.render_docx import render_docx

        output_profile = str(effective.get("output_profile") or "memo")
        layout = dict(
            effective.get("text_layout" if output_profile == "text" else "memo_layout") or {}
        )
        if args.header_text:
            layout["header_text"] = args.header_text
        render_docx(
            result,
            args.output,
            title=args.title,
            user=args.user,
            profile=output_profile,
            layout=layout,
        )
    if args.pdf:
        from auditcore_documents.render_pdf import render_synopsis_pdf, synopsis_report

        args.pdf.write_bytes(
            render_synopsis_pdf(
                args.title or f"Vergleich: {result.old_filename} / {result.new_filename}",
                synopsis_report(result),
            )
        )
    data = result.to_dict()
    if args.json:
        args.json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "create-config":
            save_settings({}, args.path)
            sys.stdout.write(f"Einstellungen angelegt: {args.path}\n")
            return 0
        if args.command == "read":
            mode, items = read_document(args.path, args.mode)
            payload = {"mode": mode, "items": [asdict(item) for item in items]}
            sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            return 0
        data = _compare(args)
    except (CompareError, ValueError) as exc:
        sys.stderr.write(f"Fehler: {exc}\n")
        return 2
    sys.stdout.write(
        f"geändert={data['changed_count']} entfallen={data['removed_count']} "
        f"neu={data['added_count']} umgestellt={data['moved_count']}\n"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
