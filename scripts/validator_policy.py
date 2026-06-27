"""
@meta
name: validator_policy
type: module
domain: docs
distribution_tier: starter_kit
responsibility:
  - Centralize validator-owned adoption-shape policy constants and field registries.
  - Keep schema, template, and canonical-style rule data separate from validator flow logic.
inputs:
  - Internal validator policy maintained in code.
outputs:
  - Shared constants imported by validator scripts.
tags:
  - docs
  - validation
  - policy
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

from collections.abc import Mapping

# Adoption and folder surface policy.
ALLOWED_MODES = {
    "starter_method_only",
    "managed_architecture_metadata",
    "legacy_compatibility",
    "consumer_starter_mode",
    "source_of_truth_owner",
    "legacy_compatibility_mode",
}
ADOPTION_MODE_ALIASES = {
    "consumer_starter_mode": "starter_method_only",
    "source_of_truth_owner": "managed_architecture_metadata",
    "legacy_compatibility_mode": "legacy_compatibility",
}
ALLOWED_REPO_ROLES = {
    "source_owner",
    "consumer_derived",
}
DEFAULT_REPO_ROLE = "source_owner"
METHOD_FEATURE_IDS = {"repo-operating-system"}
METHOD_FEATURE_PREFIXES = (
    "repo-",
    "agent-",
    "adapter-",
    "publication-",
    "docs-governance",
)
REQUIRED_PROJECT_FOLDERS = (
    "docs/intent",
    "docs/operating_system",
    "docs/superpowers/specs",
    "docs/superpowers/plans",
    "repo_config",
    "scripts",
    "tests",
)
REQUIRED_STARTER_SYNC_SURFACE_CLASSES = {
    "repo_config",
    "operating_system_docs",
    "skills",
    "adapters",
    "generated_instruction_surfaces",
    "validation_and_sync_scripts",
}
ALLOWED_STARTER_SYNC_STATUSES = {"aligned", "customized", "deferred", "not_applicable"}

# Required and optional root-doc policy.
REQUIRED_ROOT_PROJECT_DOCS = (
    "docs/setup.md",
    "docs/configuration.md",
    "docs/usage.md",
    "docs/pipeline.md",
    "docs/architecture.md",
)
MANAGED_REQUIRED_ROOT_DOC_METADATA = {
    "docs/setup.md": {
        "doc_id": "setup",
        "required_explain_groups": ("features", "stages"),
        "missing_explains_message": "Setup doc must explain one or more features or stages.",
        "missing_explains_fix": (
            "Add an `explains.features` or `explains.stages` list so setup guidance remains "
            "linked to the managed architecture surface."
        ),
    },
    "docs/configuration.md": {
        "doc_id": "configuration",
        "required_explain_groups": ("features", "configs"),
        "missing_explains_message": "Configuration doc must explain one or more features or configs.",
        "missing_explains_fix": (
            "Add an `explains.features` or `explains.configs` list so configuration guidance "
            "maps back to the managed config surface."
        ),
    },
    "docs/usage.md": {
        "doc_id": "usage",
        "required_explain_groups": ("features", "stages"),
        "missing_explains_message": "Usage doc must explain one or more features or stages.",
        "missing_explains_fix": (
            "Add an `explains.features` or `explains.stages` list so operator usage stays "
            "linked to the managed architecture surface."
        ),
    },
    "docs/pipeline.md": {
        "doc_id": "pipeline",
        "required_explain_groups": ("stages",),
        "missing_explains_message": "Pipeline doc must explain one or more stages.",
        "missing_explains_fix": (
            "Add an `explains.stages` list so pipeline guidance stays grounded in the stage "
            "contracts instead of prose only."
        ),
    },
    "docs/architecture.md": {
        "doc_id": "architecture",
        "required_explain_groups": ("features", "stages", "components"),
        "missing_explains_message": "Architecture doc must explain one or more features, stages, or components.",
        "missing_explains_fix": (
            "Add at least one of `explains.features`, `explains.stages`, or `explains.components` "
            "so architecture guidance is anchored to managed architecture surfaces."
        ),
    },
}
MANAGED_OPTIONAL_ROOT_DOC_METADATA = {
    "docs/dataset.md": {
        "doc_id": "dataset",
        "required_explain_groups": ("features", "stages", "configs"),
        "missing_explains_message": "Dataset doc must explain one or more features, stages, or configs.",
        "missing_explains_fix": (
            "Add an `explains.features`, `explains.stages`, or `explains.configs` list so "
            "dataset guidance is linked to the managed architecture surface."
        ),
    },
    "docs/api.md": {
        "doc_id": "api",
        "required_explain_groups": ("features", "capabilities", "components"),
        "missing_explains_message": "API doc must explain one or more features, capabilities, or components.",
        "missing_explains_fix": (
            "Add an `explains.features`, `explains.capabilities`, or `explains.components` list "
            "so API guidance is linked to the managed architecture surface."
        ),
    },
    "docs/observability.md": {
        "doc_id": "observability",
        "required_explain_groups": ("features", "stages", "configs", "components"),
        "missing_explains_message": (
            "Observability doc must explain one or more features, stages, configs, or components."
        ),
        "missing_explains_fix": (
            "Add an `explains.features`, `explains.stages`, `explains.configs`, or "
            "`explains.components` list so observability guidance is linked to the managed surface."
        ),
    },
    "docs/testing.md": {
        "doc_id": "testing",
        "required_explain_groups": ("features", "capabilities", "stages"),
        "missing_explains_message": "Testing doc must explain one or more features, capabilities, or stages.",
        "missing_explains_fix": (
            "Add an `explains.features`, `explains.capabilities`, or `explains.stages` list so "
            "testing guidance is linked to the managed verification surface."
        ),
    },
}
REQUIRED_DOC_KEYWORDS = {
    "docs/setup.md": ("depend", "tool version", "install", "provision", "prerequisite", "bootstrap"),
    "docs/configuration.md": (
        "environment variable",
        "config file",
        "profile",
        "default",
        "override",
        "ownership",
        "repo_config",
        "configs",
    ),
    "docs/usage.md": ("command", "entrypoint", "run flow", "workflow", "operator", "developer flow", "run loop"),
    "docs/pipeline.md": ("stage", "workflow", "step", "handoff", "processing flow", "sequence"),
    "docs/architecture.md": ("component", "boundar", "integration", "information flow", "control flow"),
}
PLACEHOLDER_PATTERNS = ("todo", "tbd", "placeholder", "fill this in later")
MODE_A_DISCOVERY_CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx"}
MODE_A_DISCOVERY_RUNTIME_DIRS = ("src", "app")
MODE_A_DISCOVERY_TEST_DIRS = ("tests",)
MODE_A_DISCOVERY_MIN_RUNTIME_CODE_FILES = 2
MODE_A_DISCOVERY_MIN_TEST_CODE_FILES = 1
MODE_A_DISCOVERY_API_PATH_HINTS = ("api", "server", "router", "route", "endpoint", "http")
MODE_A_OUTGROWN_MIN_RUNTIME_CODE_FILES = 10
MODE_A_OUTGROWN_MIN_TEST_CODE_FILES = 5
MODE_A_OUTGROWN_MIN_RUNTIME_BREADTH_DIRS = 3

# Generated schema and feature/stage contract policy.
GENERATED_INDEX_NAMES = {
    "architecture_dag.yaml",
    "capability_lineage.yaml",
    "feature_capabilities_index.yaml",
    "feature_dependency_graph.yaml",
    "feature_overview.md",
    "features_by_status.yaml",
    "features_index.yaml",
}
FEATURE_CONTRACT_REQUIRED_KEYS = {
    "feature_id",
    "name",
    "status",
    "type",
    "summary",
    "invariants",
    "domains",
    "depends_on",
    "capabilities",
    "refs",
}
FEATURE_CONTRACT_REF_KEYS = {
    "code",
    "tests",
    "specs",
    "plans",
    "docs",
    "configs",
    "components",
}
FEATURE_CONTRACT_FRESHNESS_KEYS = {
    "revision",
    "latest_change_id",
    "last_updated_at",
}
FEATURE_CONTRACT_STRING_FIELDS = {
    "feature_id",
    "name",
    "status",
    "type",
    "summary",
}
FEATURE_CONTRACT_INVARIANT_REQUIRED_KEYS = {
    "invariant_id",
    "statement",
    "state",
}
FEATURE_CONTRACT_CAPABILITY_REQUIRED_KEYS = {
    "capability_id",
    "statement",
    "state",
}
STAGE_CONTRACT_REQUIRED_KEYS = {
    "stage_id",
    "name",
    "status",
    "purpose",
    "feature_refs",
    "capability_refs",
    "code_refs",
    "test_refs",
    "doc_refs",
    "config_refs",
    "component_refs",
}
STAGE_CONTRACT_STRING_LIST_OPTIONAL_KEYS = {
    "depends_on",
    "hands_off_to",
    "inputs",
    "outputs",
    "invariants",
    "human_notes",
}
CAPABILITY_LINEAGE_REQUIRED_KEYS = {"features"}
ARCHITECTURE_DAG_REQUIRED_KEYS = {"nodes", "edges"}
REQUIRED_LINEAGE_TOP_LEVEL_KEYS = {"feature_id", "source", "invariants", "capabilities", "timeline"}
LEGACY_LINEAGE_TOP_LEVEL_KEYS = {
    "generated_contract",
    "naming_policy",
    "capability_shape",
    "capability_ids",
    "refs",
    "refs_by_type",
}
LINEAGE_REQUIRED_CAPABILITY_KEYS = {
    "state",
    "statement",
    "satisfies",
    "code",
    "tests",
    "docs",
    "docs_evidence",
    "configs",
    "config_evidence",
    "components",
    "component_evidence",
    "specs",
    "plans",
    "evidence_gaps",
    "allowed_evidence_gaps",
    "lineage_exception_reason",
    "unresolved_evidence_gaps",
    "completeness_status",
}
LINEAGE_RICH_TIMELINE_KEYS = {
    "completed_at",
    "source_plan",
    "change_id",
    "summary",
    "capabilities",
    "verification",
    "outcome",
}
LINEAGE_COMPLETENESS_STATUSES = {"complete", "excepted", "incomplete"}

# Shared repo-contract marker policy.
GENERATED_HISTORY_START_MARKER = "<!-- GENERATED HISTORY START -->"
GENERATED_HISTORY_END_MARKER = "<!-- GENERATED HISTORY END -->"
HUMAN_NOTES_HEADING = "## Human Notes"
ARCHITECTURE_METADATA_MARKER_LINE = "# @architecture"
SETUP_META_MARKER = "@meta"
STARTER_KIT_DISTRIBUTION_TIER = "starter_kit"
STARTER_KIT_CLASSIFICATION_ENFORCEMENT = "fail"
FORBIDDEN_MANUAL_REFS_FIELD = "manual_refs"
MANUAL_REFS_REMEDIATION = (
    "add ownership metadata to code, tests, docs, specs, plans, configs, or "
    "components instead"
)


def feature_source_has_forbidden_manual_refs(payload: object) -> bool:
    return isinstance(payload, Mapping) and FORBIDDEN_MANUAL_REFS_FIELD in payload


def format_manual_refs_forbidden_message(*, owner: str | None = None) -> str:
    message = (
        f"{FORBIDDEN_MANUAL_REFS_FIELD} is no longer supported; "
        f"{MANUAL_REFS_REMEDIATION}"
    )
    if owner is None:
        return message
    return f"{owner}: {message}"


# Template and metadata-scan policy.
MODE_A_TEMPLATE_SPEC_PATH = "docs/superpowers/specs/2026-04-23-mode-a-project-template-pack-spec.md"
MODE_A_TEMPLATE_ROOT = "docs/project_templates/mode-a"
MODE_A_TEMPLATE_REQUIRED_FILES = (
    "README.md",
    "docs/setup.md",
    "docs/configuration.md",
    "docs/usage.md",
    "docs/pipeline.md",
    "docs/architecture.md",
    "docs/intent/README.md",
    "docs/intent/project-charter.md",
    "docs/intent/constraints-and-non-goals.md",
    "docs/intent/stakeholders.md",
    "docs/intent/success-outcomes.md",
    "repo_config/adoption-mode.yaml",
    "repo_config/publication-config.json",
    "repo_config/agent-adapter-mappings.json",
    "configs/starter-runtime.yaml",
    "scripts/README.md",
    "tests/README.md",
)
MODE_A_TEMPLATE_MANAGED_MARKERS = (
    "@capability",
    "@proves",
    "feature.source.yaml",
    "stage.source.yaml",
    "explains.features",
    "capability_id:",
    "capability_ids:",
)
MANAGED_FEATURE_TEMPLATE_PATH = "docs/architecture_templates/feature.source.yaml"
YAML_ARCHITECTURE_TEMPLATE_PATH = "docs/architecture_templates/yaml-architecture.yaml"
MARKDOWN_FRONTMATTER_TEMPLATE_PATH = "docs/architecture_templates/markdown-frontmatter.md"
METADATA_SCAN_SUFFIXES = {".py", ".yaml", ".yml", ".sql", ".md"}
METADATA_SCAN_SKIP_DIRS = {
    ".git",
    ".tmp-tests",
    ".venv",
    ".agents",
    "venv",
    "node_modules",
    "generated_agents",
    "docs",
    "agent-core",
    "repo_config",
    "scripts",
    "tests",
    "tools",
}
FEATURE_METADATA_PATTERNS = (
    "@capability",
    "@proves",
    "explains.features",
    "capability_id:",
    "capability_ids:",
)


def normalize_adoption_mode(mode: str | None) -> str | None:
    if mode is None:
        return None
    normalized = mode.strip()
    if not normalized:
        return None
    return ADOPTION_MODE_ALIASES.get(normalized, normalized)
