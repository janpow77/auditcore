#!/usr/bin/env python3
"""Build the auditcore library Debian package from the same release's wheel."""

import argparse
from pathlib import Path

from auditcore.tools.common import emit, read_json
from auditcore.tools.deployer.library import build_library_deb


def main() -> None:
    """Parse explicit reproducibility and Debian ownership metadata."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--output", type=Path, default=Path("dist/library"))
    parser.add_argument("--source-date-epoch", type=int, required=True)
    parser.add_argument("--maintainer", required=True)
    parser.add_argument(
        "--dependency-mapping",
        type=Path,
        help="JSON mapping exact Requires-Dist strings to Debian dependencies",
    )
    parser.add_argument(
        "--allow-unreviewed-license",
        action="store_true",
        help="Local test build only; mark publication blocked for unknown licenses",
    )
    args = parser.parse_args()
    emit(
        build_library_deb(
            args.wheel,
            args.output,
            source_date_epoch=args.source_date_epoch,
            maintainer=args.maintainer,
            allow_unreviewed_license=args.allow_unreviewed_license,
            dependency_mapping=read_json(args.dependency_mapping)
            if args.dependency_mapping
            else None,
        )
    )


if __name__ == "__main__":
    main()
