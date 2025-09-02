from core.schemas import ConceptBrief, Plan, RoleCard, ScopeNote, Task, TaskSpec


def test_scope_note_instantiation():
    note = ScopeNote(
        idea="Idea",
        constraints=["C1"],
        time_budget_hours=1.0,
        cost_budget_usd=10.0,
        risk_posture="low",
        redaction_rules=["email"],
    )
    assert note.idea == "Idea"


def test_concept_brief_instantiation():
    brief = ConceptBrief(
        problem="P",
        value="V",
        users=["user"],
        success_metrics=["metric"],
        risks=["risk"],
        cost_range="0-1",
    )
    assert brief.value == "V"


def test_role_card_instantiation():
    card = RoleCard(
        role="R",
        responsibilities=["do"],
        inputs=["in"],
        outputs=["out"],
    )
    assert card.role == "R"


def test_task_spec_instantiation():
    task = TaskSpec(role="R", task="Do")
    assert task.task == "Do"


def test_plan_requires_id_and_summary():
    plan = Plan(tasks=[Task(id="T1", title="R", summary="S")])
    assert plan.tasks[0].id == "T1"
