"""Build a static PEP 503 package index from downloaded GitHub release assets.

The index only links to the immutable release assets (``<base-url>/<tag>/<file>``)
with their SHA-256; it hosts no files itself. Expected input layout::

    <assets>/<tag>/<distribution files>

Only wheels and sdists are indexed. When a file name occurs in several
releases the newest release wins. A differing wheel fails the build; a sdist
may only differ in archive metadata (e.g. timestamps of a rebuild) — its
member contents must be identical, and the difference is reported.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import tarfile
import zipfile
from dataclasses import dataclass
from email.parser import BytesParser
from pathlib import Path

DEFAULT_BASE_URL = "https://github.com/janpow77/auditcore/releases/download"


@dataclass(frozen=True)
class Distribution:
    project: str
    filename: str
    url: str
    sha256: str
    requires_python: str | None


def normalize(name: str) -> str:
    """PEP 503 project name normalization."""
    return re.sub(r"[-_.]+", "-", name).lower()


def project_of(filename: str) -> str:
    if filename.endswith(".whl"):
        return normalize(filename.split("-", 1)[0])
    if filename.endswith(".tar.gz"):
        return normalize(filename[: -len(".tar.gz")].rsplit("-", 1)[0])
    raise ValueError(f"Keine Distribution: {filename}")


def requires_python(path: Path) -> str | None:
    raw: bytes | None = None
    if path.name.endswith(".whl"):
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
            raw = archive.read(names[0]) if names else None
    else:
        with tarfile.open(path, "r:gz") as archive:
            member = next(
                (
                    m
                    for m in archive.getmembers()
                    if m.name.count("/") == 1 and m.name.endswith("/PKG-INFO")
                ),
                None,
            )
            handle = archive.extractfile(member) if member else None
            raw = handle.read() if handle else None
    if raw is None:
        return None
    value = BytesParser().parsebytes(raw, headersonly=True).get("Requires-Python")
    return str(value).strip() if value else None


def _tag_key(tag: str) -> tuple[tuple[int, ...], str]:
    numbers = tuple(int(n) for n in re.findall(r"\d+", tag))
    return numbers, tag


def _sdist_members(path: Path) -> list[tuple[str, str]]:
    with tarfile.open(path, "r:gz") as archive:
        members = []
        for member in archive.getmembers():
            handle = archive.extractfile(member) if member.isfile() else None
            data = handle.read() if handle else b""
            members.append((member.name, hashlib.sha256(data).hexdigest()))
    return sorted(members)


def collect(
    assets: Path, base_url: str, notes: list[str] | None = None
) -> dict[str, list[Distribution]]:
    seen: dict[str, tuple[Distribution, Path]] = {}
    tags = sorted((p for p in assets.iterdir() if p.is_dir()), key=lambda p: _tag_key(p.name))
    for tag_dir in reversed(tags):  # newest release first
        for path in sorted(tag_dir.iterdir()):
            if not (path.name.endswith(".whl") or path.name.endswith(".tar.gz")):
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if path.name in seen:
                previous, previous_path = seen[path.name]
                if previous.sha256 == digest:
                    continue
                same_content = path.name.endswith(".tar.gz") and _sdist_members(
                    path
                ) == _sdist_members(previous_path)
                if not same_content:
                    raise ValueError(
                        f"{path.name} unterscheidet sich zwischen Releases "
                        f"({previous.url} gegenüber {tag_dir.name})."
                    )
                if notes is not None:
                    notes.append(
                        f"{path.name}: {tag_dir.name} weicht nur in Archiv-Metadaten ab; "
                        f"verlinkt ist {previous.url}."
                    )
                continue
            seen[path.name] = (
                Distribution(
                    project=project_of(path.name),
                    filename=path.name,
                    url=f"{base_url.rstrip('/')}/{tag_dir.name}/{path.name}",
                    sha256=digest,
                    requires_python=requires_python(path),
                ),
                path,
            )
    projects: dict[str, list[Distribution]] = {}
    for dist, _ in seen.values():
        projects.setdefault(dist.project, []).append(dist)
    return {
        name: sorted(dists, key=lambda d: d.filename) for name, dists in sorted(projects.items())
    }


def _page(title: str, links: list[str]) -> str:
    body = "\n".join(f"    {link}<br>" for link in links)
    return (
        "<!DOCTYPE html>\n<html>\n  <head>\n"
        '    <meta name="pypi:repository-version" content="1.0">\n'
        f"    <title>{html.escape(title)}</title>\n  </head>\n  <body>\n"
        f"{body}\n  </body>\n</html>\n"
    )


def write_index(projects: dict[str, list[Distribution]], output: Path) -> None:
    simple = output / "simple"
    simple.mkdir(parents=True, exist_ok=True)
    root_links = [f'<a href="{name}/">{html.escape(name)}</a>' for name in projects]
    (simple / "index.html").write_text(
        _page("auditcore – Paketindex", root_links), encoding="utf-8"
    )
    for name, dists in projects.items():
        links = []
        for dist in dists:
            attr = (
                f' data-requires-python="{html.escape(dist.requires_python)}"'
                if dist.requires_python
                else ""
            )
            links.append(
                f'<a href="{html.escape(dist.url)}#sha256={dist.sha256}"{attr}>'
                f"{html.escape(dist.filename)}</a>"
            )
        (simple / name).mkdir(exist_ok=True)
        (simple / name / "index.html").write_text(
            _page(f"Links für {name}", links), encoding="utf-8"
        )
    (output / ".nojekyll").write_text("", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assets", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    notes: list[str] = []
    projects = collect(args.assets, args.base_url, notes)
    if not projects:
        raise SystemExit("Keine Distributionen gefunden.")
    write_index(projects, args.output)
    for note in notes:
        print(f"Hinweis: {note}")
    print(f"{len(projects)} Projekte, {sum(len(d) for d in projects.values())} Dateien")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
