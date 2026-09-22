"""Plan-only consolidation orchestration and reuse gate."""

from __future__ import annotations

import uuid
from typing import Any

from auditcore.tools.common import now, serializable
from auditcore.tools.consolidator.analysis import detect_candidates, load_policy, load_prompt
from auditcore.tools.consolidator.inventory import GlobalInventory, JsonInventory
from auditcore.tools.consolidator.models import ConsolidationPlan, WorkflowMode
from auditcore.tools.consolidator.providers.protocols import KnowledgeStore, RepositoryProvider


class ConsolidationWorkflow:
    """Inventory, compare and plan; never transform application source."""

    def __init__(
        self, provider: RepositoryProvider, store: JsonInventory, knowledge: KnowledgeStore
    ) -> None:
        self.provider, self.store, self.knowledge = provider, store, knowledge

    def run(
        self,
        repository: str = "",
        mode: WorkflowMode = WorkflowMode.REPO_AUDITCORE,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Require inventory, expose blockers and produce independent candidate plans."""
        inventory = self.store.load("inventory_metadata")
        if not inventory or not inventory.get(
            "analysis_completed", inventory.get("status") == "COMPLETE"
        ):
            if dry_run:
                return {"status": "INVENTORY_REQUIRED", "plans": []}
            inventory = GlobalInventory(self.provider, self.store).scan_authenticated_account()
        policy = load_policy("consolidation")
        if policy["inventory_required"] and not inventory.get(
            "analysis_completed", inventory.get("status") == "COMPLETE"
        ):
            return {"status": "INVENTORY_REQUIRED", "plans": [], "inventory": inventory}
        complete_repositories = {
            r["repository"]
            for r in self.store.load("repositories")
            if r["structural_status"] == "COMPLETE"
        }
        symbols = [
            s for s in self.store.load("symbols") if s["repository"] in complete_repositories
        ]
        candidates = detect_candidates(symbols, self.store.load("repositories"))
        run_id = str(uuid.uuid4())
        plans = []
        for candidate in candidates:
            if (
                repository
                and repository not in candidate.repositories
                and mode != WorkflowMode.GLOBAL
            ):
                continue
            plans.append(
                ConsolidationPlan(
                    candidate.target_module,
                    [s["symbol"] for s in candidate.symbols],
                    candidate.symbols,
                    candidate.technical_dependencies,
                    [],
                    [] if candidate.conflict_status == "IDENTICAL" else [candidate.conflict_status],
                    [candidate.decision_status] if "HUMAN" in candidate.decision_status else [],
                    load_policy("quality")["required_verification"],
                    policy_impact=candidate.decision_status,
                    run_id=run_id,
                    metadata={
                        "requires_characterization": policy["characterization_required"],
                        "architecture_decision": "ADR-001-multi-package-monorepo",
                        "license_status": candidate.license_status,
                        "verified_consumers": candidate.consumers,
                        "potential_consumers": candidate.potential_consumers,
                        "consumer_status": candidate.consumer_status,
                        "origin_groups": candidate.origin_groups,
                        "origin_evidence": candidate.origin_evidence,
                        "independent_origins_status": candidate.independent_origins_status,
                        "runtime_dependencies_status": "REVIEW_REQUIRED",
                        "platform_runtime_dependency_required": False,
                    },
                    target_distribution=candidate.target_distribution,
                    package_directory=candidate.package_directory,
                )
            )
        result = {
            "run_id": run_id,
            "started_at": now(),
            "mode": mode,
            "status": "PLANNED",
            "plans": serializable(plans),
            "prompt_versions": {
                name: {k: v for k, v in load_prompt(name).items() if k != "content"}
                for name in ("consolidation", "conflict_analysis")
            },
            "policy_versions": {"consolidation": policy["policy_version"]},
            "input_commit": inventory.get("repository_revision"),
            "output_commit": None,
            "tool_versions": {"auditcore": "0.1.0"},
        }
        if not dry_run:
            self.store.save("plans", result)
        return result
