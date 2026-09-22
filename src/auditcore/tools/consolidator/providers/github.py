"""GitHub provider using existing gh credentials, never printing tokens."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from auditcore.tools.common import run
from auditcore.tools.consolidator.models import RepositoryRecord


class GitHubProvider:
    """Paginated GitHub discovery and sparse immutable Git source checkouts."""

    def __init__(self, cache: Path = Path(".auditcore/repositories")) -> None:
        self.cache = cache.resolve()

    def repositories(self) -> list[RepositoryRecord]:
        """Inventory owned, organization and collaborator repositories."""
        login = run(["gh", "api", "user", "--jq", ".login"]).strip()
        pages = []
        page_number = 1
        while True:
            page = json.loads(
                run(
                    [
                        "gh",
                        "api",
                        f"/user/repos?per_page=100&page={page_number}"
                        "&affiliation=owner,collaborator,organization_member",
                    ]
                )
            )
            pages.append(page)
            if len(page) < 100:
                break
            page_number += 1
        records = []
        seen = set()
        for row in (r for page in pages for r in page):
            if row["full_name"] in seen:
                continue
            seen.add(row["full_name"])
            owner = row["owner"]["login"]
            records.append(
                RepositoryRecord(
                    row["full_name"],
                    owner,
                    row["visibility"],
                    row["default_branch"],
                    row["archived"],
                    row["fork"],
                    row["language"],
                    license=(row.get("license") or {}).get("spdx_id", "UNKNOWN"),
                    source_url=row["html_url"],
                    structural_status="NOT_APPLICABLE_WITH_REASON"
                    if row.get("size") == 0
                    else "NOT_EXECUTED",
                    reason="Empty GitHub repository (size=0)" if row.get("size") == 0 else "",
                    affiliation="OWNED"
                    if owner == login
                    else "ORGANIZATION"
                    if row["owner"]["type"] == "Organization"
                    else "COLLABORATOR",
                )
            )
        return sorted(records, key=lambda r: r.repository.lower())

    def metadata(self, record: RepositoryRecord) -> None:
        """Resolve live default-branch SHA and language information."""
        record.commit_sha = run(
            [
                "gh",
                "api",
                f"repos/{record.repository}/commits/{record.default_branch}",
                "--jq",
                ".sha",
            ]
        ).strip()
        languages: dict[str, Any] = json.loads(
            run(
                [
                    "gh",
                    "api",
                    f"repos/{record.repository}/languages",
                ]
            )
        )
        record.languages = sorted(languages)

    def checkout(self, repository: RepositoryRecord) -> Path:
        """Fetch code-only sparse source without running repository code."""
        target = self.cache / repository.repository.replace("/", "__")
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--filter=blob:none",
                    "--no-checkout",
                    f"https://github.com/{repository.repository}.git",
                    str(target),
                ],
                timeout=300,
            )
        try:
            run(["git", "cat-file", "-e", repository.commit_sha], target)
        except RuntimeError:
            run(
                ["git", "fetch", "--depth", "1", "origin", repository.commit_sha],
                target,
                timeout=300,
            )
        patterns = [
            "*.py",
            "*.pyi",
            "*.js",
            "*.ts",
            "*.tsx",
            "*.jsx",
            "*.vue",
            "*.bas",
            "*.cls",
            "*.toml",
            "requirements*.txt",
            "setup.cfg",
            "package.json",
            "*LICENSE*",
            "*license*",
            "*.yml",
            "*.yaml",
            "*.ini",
            "Dockerfile*",
            "!**/node_modules/",
            "!**/.venv/",
            "!**/dist/",
            "!**/vendor/",
            "!**/build/",
            "!**/package-lock.json",
        ]
        result = subprocess.run(
            ["git", "sparse-checkout", "set", "--no-cone", "--stdin"],
            cwd=target,
            input="\n".join(patterns),
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
        )
        if result.returncode:
            raise RuntimeError("Sparse checkout failed")
        run(["git", "checkout", "--detach", repository.commit_sha], target, timeout=300)
        return target
