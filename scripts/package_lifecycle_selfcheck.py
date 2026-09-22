"""Real lifecycle tests of explicitly synthetic Debian fixtures, never a product release."""

from __future__ import annotations

import json
from pathlib import Path

from auditcore.tools.apprefactor.engine import source_digest
from auditcore.tools.common import write_json
from auditcore.tools.deployer.build import DeploymentBuilder
from auditcore.tools.deployer.validation import DockerPackageTester


def main() -> None:
    """Reuse the pytest-created fixture and execute real install/upgrade/remove/health checks."""
    roots = list(Path(".auditcore/package-fixtures").glob("test_deb_build*/application"))
    if not roots:
        raise SystemExit("Run pytest tests/test_deployer.py --basetemp=.auditcore/package-fixtures")
    root = roots[0]
    (root / "src/main.py").write_text(
        '"""Synthetic health fixture; no business data."""\n'
        "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
        "class Health(BaseHTTPRequestHandler):\n"
        "    def do_GET(self):\n"
        '        self.send_response(200 if self.path == "/health" else 404)\n'
        "        self.end_headers()\n"
        '        self.wfile.write(b"ready")\n'
        'HTTPServer(("127.0.0.1", 18089), Health).serve_forever()\n'
    )
    configuration = json.loads((root / "auditcore-deploy.json").read_text())
    configuration["health_url"] = "http://127.0.0.1:18089/health"
    handoff = json.loads((root / ".auditcore/deployment-handoff.json").read_text())
    packages = []
    for version in ("1.0.0", "1.1.0"):
        configuration["version"] = version
        write_json(root / "auditcore-deploy.json", configuration)
        configuration["source_digest"] = source_digest(root)
        write_json(root / "auditcore-deploy.json", configuration)
        handoff["source_digest"] = source_digest(root)
        write_json(root / ".auditcore/deployment-handoff.json", handoff)
        result = DeploymentBuilder().build_application(root, Path(".auditcore/package-lifecycle"))
        packages.append(Path(result.package))
    tester = DockerPackageTester()
    installation = tester.test(packages[0])
    upgrade = tester.test_upgrade(*packages)
    write_json(
        Path(".auditcore/package-lifecycle-result.json"),
        {
            "fixture_gate_inputs_are_synthetic": True,
            "scope": "Actual isolated Debian package lifecycle; no production authorization",
            "installation": installation,
            "upgrade": upgrade,
        },
    )
    print(installation)
    print(upgrade)


if __name__ == "__main__":
    main()
