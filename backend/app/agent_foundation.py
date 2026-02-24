from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath


class RunPhase(str, Enum):
    QUEUED = "queued"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_USER = "waiting_user"
    SUCCESS = "success"
    FAILED = "failed"


_ALLOWED_TRANSITIONS: dict[RunPhase, set[RunPhase]] = {
    RunPhase.QUEUED: {RunPhase.PLANNING, RunPhase.RUNNING, RunPhase.FAILED},
    RunPhase.PLANNING: {RunPhase.RUNNING, RunPhase.WAITING_USER, RunPhase.FAILED},
    RunPhase.RUNNING: {RunPhase.WAITING_USER, RunPhase.SUCCESS, RunPhase.FAILED},
    RunPhase.WAITING_USER: {RunPhase.RUNNING, RunPhase.FAILED},
    RunPhase.SUCCESS: set(),
    RunPhase.FAILED: set(),
}


@dataclass(frozen=True)
class SkillSpec:
    name: str
    version: str
    input_types: tuple[str, ...]
    output_types: tuple[str, ...]


def can_transition(current: RunPhase, next_phase: RunPhase) -> bool:
    return next_phase in _ALLOWED_TRANSITIONS[current]


def validate_output_path(path: str) -> bool:
    candidate = PurePosixPath(path)
    if candidate.is_absolute():
        return False
    parts = candidate.parts
    if not parts or parts[0] != "out":
        return False
    if ".." in parts:
        return False
    return True


def validate_raw_read_path(path: str) -> bool:
    candidate = PurePosixPath(path)
    if candidate.is_absolute():
        return False
    parts = candidate.parts
    if not parts or parts[0] != "raw":
        return False
    if ".." in parts:
        return False
    return True


def build_default_skill_catalog() -> dict[str, SkillSpec]:
    return {
        "ppt_revise": SkillSpec(
            name="ppt_revise",
            version="0.1",
            input_types=("pptx", "pdf", "text"),
            output_types=("pptx",),
        ),
        "doc_analyze": SkillSpec(
            name="doc_analyze",
            version="0.1",
            input_types=("pdf", "pptx", "xlsx", "text"),
            output_types=("text",),
        ),
    }


def is_supported_skill(skill_name: str, catalog: dict[str, SkillSpec] | None = None) -> bool:
    catalog_to_use = catalog or build_default_skill_catalog()
    return skill_name in catalog_to_use
