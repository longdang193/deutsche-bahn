from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_scope_and_bronze_extraction.py'
SCRIPTS_ROOT = str(REPO_ROOT / 'scripts')

if SCRIPTS_ROOT not in sys.path:
    sys.path.insert(0, SCRIPTS_ROOT)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load {path.name}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BRONZE = load_module('run_scope_and_bronze_extraction', SCRIPT_PATH)


def test_parse_month_bounds_handles_month_end() -> None:
    month_start, month_end = BRONZE.parse_month_bounds('data-2025-02.parquet')

    assert month_start.isoformat() == '2025-02-01'
    assert month_end.isoformat() == '2025-02-28'


def test_build_month_source_version_and_url_are_deterministic() -> None:
    file_name = 'data-2025-04.parquet'

    assert BRONZE.build_month_source_version(file_name) == 'monthly_processed_data/data-2025-04.parquet@main'
    assert BRONZE.build_month_source_url(file_name).endswith('/monthly_processed_data/data-2025-04.parquet')


def test_scope_config_stays_input_only() -> None:
    config = BRONZE.load_scope_config(REPO_ROOT / 'config' / 'scope.yml')

    assert not hasattr(config, 'added_week_source_file_name')
    assert not hasattr(config, 'added_week_start_date')
