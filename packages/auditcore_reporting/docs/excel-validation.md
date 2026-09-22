# Excel 0.2.0 verification

The unchanged MIT Flowlib source at aca2dc6aad25aea0720312dbcc6da00b0bcba330
was executed before adaptation. Five workbook snapshots preserve ordinary values,
styles, column widths, empty tables, offset headers and NaN handling. The existing
34 number-format observations remain unchanged. Formula-like strings deliberately
become inert text rather than executable formulas.

The Office XML skill validator reproduced two font-element ordering errors in
openpyxl output. The adapter now orders only generated xl/styles.xml font
properties; all property values, worksheets and relationships remain preserved.
The regression test reads back fonts, data and the exact schema order.

Actual local checks on 2026-09-22: 88 pytest tests passed, Ruff passed, strict Mypy
passed for six source files. An actual workbook containing text, a formula-like
string, amounts and dates passed ZIP/XML package checking and Microsoft365 Open
XML SDK schema validation, with zero package and schema errors. This is no claim
of a native Microsoft Excel opening or visual layout test.

The optional extra uses openpyxl and defusedxml. Core imports and number-format
rules remain standard-library-only. The optional installed smoke exercises data,
formatting, dates and formula injection after building and installing the wheel.
