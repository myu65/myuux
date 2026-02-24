from app.agent_foundation import (
    RunPhase,
    build_default_skill_catalog,
    can_transition,
    is_supported_skill,
    validate_output_path,
    validate_raw_read_path,
)


def test_run_phase_transition_rules() -> None:
    assert can_transition(RunPhase.QUEUED, RunPhase.PLANNING)
    assert can_transition(RunPhase.RUNNING, RunPhase.SUCCESS)
    assert not can_transition(RunPhase.SUCCESS, RunPhase.RUNNING)


def test_workspace_path_policy() -> None:
    assert validate_raw_read_path("raw/input/source.pdf")
    assert not validate_raw_read_path("out/generated.pdf")
    assert validate_output_path("out/generated/report.pdf")
    assert not validate_output_path("raw/generated/report.pdf")
    assert not validate_output_path("../out/escape.pdf")


def test_default_skill_catalog_supports_expected_skills() -> None:
    catalog = build_default_skill_catalog()

    assert "ppt_revise" in catalog
    assert "doc_analyze" in catalog
    assert is_supported_skill("ppt_revise", catalog)
    assert not is_supported_skill("unknown_skill", catalog)
