"""Versionsvergleich, Soll/Ist-Abgleich und Einfärben von Diagrammen."""

from .coloring import apply_colors, colors_from_markers
from .diff import DIFF_COLORS, Change, Comparison, compare
from .matching import match_elements
from .target_actual import TargetActualComparison, TargetActualResult, compare_target_actual

__all__ = [
    "DIFF_COLORS",
    "Change",
    "Comparison",
    "TargetActualComparison",
    "TargetActualResult",
    "apply_colors",
    "colors_from_markers",
    "compare",
    "compare_target_actual",
    "match_elements",
]
