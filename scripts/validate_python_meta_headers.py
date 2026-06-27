"""
@meta
name: validate_python_meta_headers
type: script
domain: validation
distribution_tier: starter_kit
responsibility:
  - Validate module-level Python @meta docstring blocks for governed source folders.
  - Enforce required metadata keys and basic shape constraints.
  - Optionally enforce capability linkage against feature source capability IDs.
inputs:
  - Python files under configured scan roots
  - Feature source files declaring capability_id values
outputs:
  - Exit status and validation report
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path

REQUIRED_KEYS = {
    "name",
    "type",
    "domain",
    "responsibility",
    "inputs",
    "outputs",
    "lifecycle",
}

CAPABILITY_ID_PATTERN = re.compile(r"^\s*-?\s*capability_id\s*:\s*([A-Za-z0-9._-]+)\s*$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Python @meta docstring headers.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument(
        "--paths",
        nargs="*",
        default=["src"],
        help="Relative directories to scan for Python files.",
    )
    parser.add_argument(
        "--enforce-capability-linkage",
        action="store_true",
        help="Validate @meta.capabilities entries against feature.source.yaml capability_id values.",
    )
    parser.add_argument(
        "--require-ownership",
        action="store_true",
        help="Require @meta.ownership with value feature or infrastructure.",
    )
    parser.add_argument(
        "--require-feature-capabilities",
        action="store_true",
        help="Require @meta.capabilities when @meta.ownership is feature.",
    )
    return parser


def _extract_module_docstring(path: Path) -> str | None:
    try:
        module = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return ast.get_docstring(module, clean=False)


def _parse_meta_lines(docstring: str) -> dict[str, str | list[str]]:
    result: dict[str, str | list[str]] = {}
    lines = [line.rstrip() for line in docstring.splitlines()]
    if not lines or lines[0].strip() != "@meta":
        return result

    current_key: str | None = None
    for raw in lines[1:]:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("- ") and current_key:
            result.setdefault(current_key, [])
            if isinstance(result[current_key], list):
                result[current_key].append(line[2:].strip())
            continue
        if current_key and raw.startswith((" ", "\t")) and ":" in line:
            result.setdefault(current_key, [])
            if isinstance(result[current_key], list):
                result[current_key].append(line)
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            if value:
                result[current_key] = value
            else:
                result[current_key] = []
    return result


def _collect_known_capability_ids(root: Path) -> set[str]:
    capability_ids: set[str] = set()
    for path in root.glob("docs/features/**/feature.source.yaml"):
        try:
            content = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in content:
            match = CAPABILITY_ID_PATTERN.match(line)
            if match:
                capability_ids.add(match.group(1).strip())
    return capability_ids


def validate_python_meta_headers(
    root: Path,
    relative_paths: list[str],
    enforce_capability_linkage: bool = False,
    require_ownership: bool = False,
    require_feature_capabilities: bool = False,
) -> list[str]:
    issues: list[str] = []
    targets: list[Path] = []
    for rel in relative_paths:
        base = root / rel
        if base.exists():
            targets.extend(sorted(base.rglob("*.py")))

    known_capability_ids = _collect_known_capability_ids(root) if enforce_capability_linkage else set()

    for path in targets:
        doc = _extract_module_docstring(path)
        rel = path.relative_to(root).as_posix()
        if not doc:
            issues.append(f"{rel}: missing module docstring with @meta block")
            continue
        parsed = _parse_meta_lines(doc)
        if not parsed:
            issues.append(f"{rel}: missing or malformed @meta block")
            continue
        for key in REQUIRED_KEYS:
            if key not in parsed:
                issues.append(f"{rel}: missing @meta required key `{key}`")

        lifecycle = parsed.get("lifecycle")
        if isinstance(lifecycle, list):
            if not any(item.strip().startswith("status:") for item in lifecycle if isinstance(item, str)):
                issues.append(f"{rel}: `lifecycle` must include `status`")

        ownership = parsed.get("ownership")
        if require_ownership:
            if ownership not in {"feature", "infrastructure"}:
                issues.append(f"{rel}: `ownership` must be `feature` or `infrastructure`")

        capabilities = parsed.get("capabilities")
        capability_entries = capabilities if isinstance(capabilities, list) else []

        if require_feature_capabilities and ownership == "feature" and not capability_entries:
            issues.append(f"{rel}: `ownership: feature` requires non-empty `capabilities`")

        if enforce_capability_linkage and capability_entries:
            for capability_id in capability_entries:
                if (
                    isinstance(capability_id, str)
                    and capability_id
                    and capability_id not in known_capability_ids
                ):
                    issues.append(
                        f"{rel}: unknown @meta capability `{capability_id}` "
                        "(not found in docs/features/*/feature.source.yaml capability_id entries)"
                    )
    return issues


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo_root).resolve()
    issues = validate_python_meta_headers(
        root,
        args.paths,
        enforce_capability_linkage=args.enforce_capability_linkage,
        require_ownership=args.require_ownership,
        require_feature_capabilities=args.require_feature_capabilities,
    )
    if issues:
        print("Python @meta header validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Python @meta header validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
