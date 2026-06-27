"""
@meta
name: validate_agent_runtime_drift
type: script
domain: validation
distribution_tier: starter_kit
responsibility:
  - Validate drift across generated agent artifacts and deployed runtime targets.
  - Execute adapter sync and deploy-runtime checks in deterministic validation order.
  - Apply adoption-mode and role-aware platform scoping by default, with explicit CLI overrides.
inputs:
  - Repo root with scripts and generated adapter artifacts
  - Optional deploy drift skip flag
  - Optional platform override flags
outputs:
  - Exit status and drift validation diagnostics
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

import yaml
from validator_policy import DEFAULT_REPO_ROLE, normalize_adoption_mode


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generated/deployed agent runtime drift.")
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument(
        "--skip-deploy-check",
        action="store_true",
        help="Skip home-directory deploy drift checks.",
    )
    parser.add_argument(
        "--platform",
        action="append",
        default=[],
        help="Runtime platform to check (repeatable). Overrides mode-driven defaults unless --all-platforms is set.",
    )
    parser.add_argument(
        "--all-platforms",
        action="store_true",
        help="Check deploy drift for all runtime platforms regardless of adoption-mode policy.",
    )
    return parser.parse_args()


def _run(command: list[str], cwd: Path) -> int:
    print("> " + " ".join(command))
    return subprocess.run(command, cwd=cwd, check=False).returncode


def _read_adoption_config(root: Path) -> tuple[str, str]:
    mode_file = root / "repo_config" / "adoption-mode.yaml"
    if not mode_file.exists():
        return "managed_architecture_metadata", DEFAULT_REPO_ROLE
    payload = yaml.safe_load(mode_file.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return "managed_architecture_metadata", DEFAULT_REPO_ROLE
    mode = normalize_adoption_mode(payload.get("adoption_mode"))
    repo_role = payload.get("repo_role", DEFAULT_REPO_ROLE)
    normalized_mode = mode if isinstance(mode, str) and mode.strip() else "managed_architecture_metadata"
    normalized_role = repo_role if isinstance(repo_role, str) and repo_role.strip() else DEFAULT_REPO_ROLE
    return normalized_mode, normalized_role


def _read_adapter_sync_policy(root: Path) -> tuple[list[str], dict[str, dict[str, list[str]]]]:
    policy_file = root / "repo_config" / "adapter-sync-policy.yaml"
    if not policy_file.exists():
        return ["codex"], {}
    payload = yaml.safe_load(policy_file.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return ["codex"], {}
    defaults_raw = payload.get("default_platforms", ["codex"])
    defaults = [str(item).strip() for item in defaults_raw if str(item).strip()] if isinstance(defaults_raw, list) else ["codex"]
    mode_role_raw = payload.get("mode_role_platforms", {})
    mode_role: dict[str, dict[str, list[str]]] = {}
    if isinstance(mode_role_raw, dict):
        for role, by_mode in mode_role_raw.items():
            if not isinstance(by_mode, dict):
                continue
            mode_map: dict[str, list[str]] = {}
            for mode, platforms in by_mode.items():
                if not isinstance(platforms, list):
                    continue
                cleaned = [str(item).strip() for item in platforms if str(item).strip()]
                if cleaned:
                    mode_map[str(mode).strip()] = cleaned
            if mode_map:
                mode_role[str(role).strip()] = mode_map
    return defaults or ["codex"], mode_role


def _resolve_platform_selection(root: Path, args: argparse.Namespace) -> tuple[list[str], str]:
    if args.all_platforms:
        return ["codex", "claude", "gemini"], "all-platforms"
    cli_platforms = [
        item.strip()
        for item in (args.platform or [])
        if isinstance(item, str) and item.strip()
    ]
    if cli_platforms:
        return sorted(set(cli_platforms)), "cli-platform"
    adoption_mode, repo_role = _read_adoption_config(root)
    defaults, mode_role = _read_adapter_sync_policy(root)
    selected = mode_role.get(repo_role, {}).get(adoption_mode, [])
    if not selected:
        selected = defaults
    return sorted(set(selected)), f"mode-policy(adoption_mode={adoption_mode},repo_role={repo_role})"


def _normalize_deploy_targets(platforms: list[str]) -> tuple[list[str], list[str]]:
    canonical_targets: list[str] = []
    invalid_platforms: list[str] = []
    alias_map = {"antigravity": "gemini", "gemini": "gemini", "codex": "codex", "claude": "claude"}
    for platform in platforms:
        normalized = platform.strip().lower()
        canonical = alias_map.get(normalized)
        if canonical is None:
            invalid_platforms.append(platform)
            continue
        if canonical not in canonical_targets:
            canonical_targets.append(canonical)
    return canonical_targets, invalid_platforms


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).resolve()
    py = sys.executable
    steps = [
        [py, str(root / "scripts" / "sync_agent_adapters.py"), "--check"],
    ]
    if not args.skip_deploy_check:
        selected_platforms, selection_reason = _resolve_platform_selection(root, args)
        deploy_targets, invalid_platforms = _normalize_deploy_targets(selected_platforms)
        if invalid_platforms:
            print(
                "Invalid platform(s) for deploy drift checks: "
                + ", ".join(sorted(invalid_platforms))
                + ". Allowed platforms: codex, claude, gemini."
            )
            return 1
        if not deploy_targets:
            print("No deploy targets resolved for runtime drift checks.")
            return 1
        print("Deploy target selection: " + ", ".join(deploy_targets) + f" ({selection_reason})")
        for target in deploy_targets:
            steps.append([py, str(root / "scripts" / "deploy_agent_runtime.py"), "--target", target, "--check"])
    failures = 0
    for step in steps:
        failures += _run(step, root)
    if failures:
        print("Agent runtime drift validation failed.")
        return 1
    print("Agent runtime drift validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
