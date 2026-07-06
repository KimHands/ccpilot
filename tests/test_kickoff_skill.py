import os

SKILL = os.path.join(os.path.dirname(__file__), "..", "skills", "project-kickoff", "SKILL.md")


def _read():
    with open(SKILL, encoding="utf-8") as f:
        return f.read()


def test_frontmatter_name():
    t = _read()
    assert t.startswith("---")
    assert "name: project-kickoff" in t


def test_narrow_trigger_excludes_generic_build():
    t = _read()
    # 명시적 초기화 의도만, 일반 "X 만들거야"엔 발동 금지
    assert "Do NOT trigger" in t
    assert "만들거야" in t          # 제외 예시로 명시


def test_confirm_gate_before_writes():
    t = _read()
    assert "초기화할까요" in t
    assert "승인 전" in t or "승인하면" in t
    assert "쓰지 않는다" in t         # 확인 없이 파일 안 씀


def test_uses_dry_run_preview():
    t = _read()
    assert "--dry-run" in t
    assert "cli.py init" in t


def test_low_confidence_recommends_only():
    t = _read()
    assert "낮은 확신" in t or "낮으면" in t
    assert "추천" in t


def test_restart_notice_and_existing_project_protection():
    t = _read()
    assert "재시작" in t
    assert "project-state.json" in t
    assert "project-status" in t
