"""Frozen input assembly shared by live adapter and protocol fixture."""
from pathlib import Path


def project_root():
    return next(p for p in Path(__file__).resolve().parents if (p / '.deps/tau2-bench').is_dir())


def bundled_skill_document():
    directory = Path(__file__).resolve().parents[1] / 'skills'
    return ((directory / 'banking-mcp/SKILL.md').read_text()
            + '\n\n## Bundled business guide: dispute-processing\n\n'
            + (directory / 'dispute-processing/SKILL.md').read_text())
