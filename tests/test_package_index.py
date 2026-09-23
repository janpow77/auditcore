"""Static PEP 503 index built from release assets (synthetic fixtures)."""

import hashlib
import importlib.util
import io
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "package_index",
    Path(__file__).resolve().parents[1] / "scripts/build_package_index.py",
)
assert SPEC is not None and SPEC.loader is not None
index = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = index  # dataclasses need the module registered
SPEC.loader.exec_module(index)

METADATA = b"Metadata-Version: 2.4\nName: auditcore_geo\nVersion: 0.1.0\nRequires-Python: >=3.11\n"


def wheel(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("auditcore_geo-0.1.0.dist-info/METADATA", METADATA)


def sdist(path: Path, mtime: int = 0, extra: bytes = b"") -> None:
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo("auditcore_geo-0.1.0/PKG-INFO")
        info.size = len(METADATA + extra)
        info.mtime = mtime
        archive.addfile(info, io.BytesIO(METADATA + extra))


def test_index_links_release_assets_with_hash_and_requires_python(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    (assets / "v0.3.0").mkdir(parents=True)
    wheel(assets / "v0.3.0" / "auditcore_geo-0.1.0-py3-none-any.whl")
    sdist(assets / "v0.3.0" / "auditcore_geo-0.1.0.tar.gz")
    (assets / "v0.3.0" / "auditcore_geo-0.1.0-py3-none-any_sbom.json").write_text("{}")
    (assets / "v0.3.0" / "python3-auditcore-geo_0.1.0-1_all.deb").write_bytes(b"deb")

    projects = index.collect(assets, "https://example.invalid/download")
    index.write_index(projects, tmp_path / "site")

    assert list(projects) == ["auditcore-geo"]
    root = (tmp_path / "site/simple/index.html").read_text(encoding="utf-8")
    assert '<a href="auditcore-geo/">auditcore-geo</a>' in root
    page = (tmp_path / "site/simple/auditcore-geo/index.html").read_text(encoding="utf-8")
    digest = hashlib.sha256(
        (assets / "v0.3.0/auditcore_geo-0.1.0-py3-none-any.whl").read_bytes()
    ).hexdigest()
    assert (
        f'href="https://example.invalid/download/v0.3.0/auditcore_geo-0.1.0-py3-none-any.whl'
        f'#sha256={digest}"' in page
    )
    assert page.count('data-requires-python="&gt;=3.11"') == 2
    assert ".deb" not in page and "sbom" not in page
    assert (tmp_path / "site/.nojekyll").exists()


def test_same_file_in_two_releases_is_listed_once_newest_wins(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    for tag in ("v0.2.0", "v0.10.0"):
        (assets / tag).mkdir(parents=True)
        wheel(assets / tag / "auditcore_geo-0.1.0-py3-none-any.whl")
    projects = index.collect(assets, "https://example.invalid/download")
    assert [d.url.split("/")[-2] for d in projects["auditcore-geo"]] == ["v0.10.0"]

    (assets / "v0.2.0/auditcore_geo-0.1.0-py3-none-any.whl").write_bytes(b"anders")
    with pytest.raises(ValueError, match="unterscheidet sich"):
        index.collect(assets, "https://example.invalid/download")


def test_rebuilt_sdist_may_differ_only_in_archive_metadata(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    for tag, mtime in (("v0.1.0", 1), ("v0.2.0", 2)):
        (assets / tag).mkdir(parents=True)
        sdist(assets / tag / "auditcore_geo-0.1.0.tar.gz", mtime=mtime)
    notes: list[str] = []
    projects = index.collect(assets, "https://example.invalid/download", notes)
    assert projects["auditcore-geo"][0].url.endswith("/v0.2.0/auditcore_geo-0.1.0.tar.gz")
    assert len(notes) == 1 and "Archiv-Metadaten" in notes[0]

    sdist(assets / "v0.1.0/auditcore_geo-0.1.0.tar.gz", extra=b"X")
    with pytest.raises(ValueError, match="unterscheidet sich"):
        index.collect(assets, "https://example.invalid/download")


def test_project_names_are_normalized() -> None:
    assert index.project_of("auditcore_price_sources-0.1.0.tar.gz") == "auditcore-price-sources"
    assert index.project_of("Auditcore.Geo-0.1.0-py3-none-any.whl") == "auditcore-geo"
