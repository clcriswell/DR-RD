import os
from orchestrators.spec_builder import assemble_from_agent_payloads
from utils.reportgen import render, write_csv


def test_spec_builder_outputs(tmp_path):
    answers = {
        "CTO": """```json {"requirements": ["Req1"], "interfaces": [{"name":"IF1","producer":"A","consumer":"B","contract":"C"}], "data_flows": [{"source":"A","sink":"B","data":"D"}], "next_steps": ["Do X"], "architecture": "Arch", "rollback": "Back"} ```""",
        "IP Analyst": """```json {"risks": ["Risk1"]} ```""",
        "Finance": """```json {"bom": [{"part_no":"P1","desc":"Part"}], "budget": [{"phase":"Phase1","cost_usd": 1.0}]} ```""",
        "Marketing Analyst": """```json {"milestones": ["MS1"]} ```""",
        "Research Scientist": """```json {"summary": "Overview"} ```""",
    }
    sdd, impl = assemble_from_agent_payloads("Proj", "Idea", answers)
    assert sdd.requirements and impl.work
    out_dir = tmp_path / "audits" / "proj" / "build"
    os.makedirs(out_dir, exist_ok=True)
    open(out_dir / "SDD.md", "w", encoding="utf-8").write(
        render("build/SDD.md.j2", {"sdd": sdd})
    )
    open(out_dir / "ImplementationPlan.md", "w", encoding="utf-8").write(
        render("build/ImplementationPlan.md.j2", {"impl": impl})
    )
    write_csv(
        out_dir / "bom.csv",
        [b.model_dump() for b in impl.bom],
        headers=["part_no", "desc", "qty", "unit_cost", "vendor"],
    )
    write_csv(
        out_dir / "budget.csv",
        [b.model_dump() for b in impl.budget],
        headers=["phase", "cost_usd"],
    )
    os.makedirs(out_dir / "interface_contracts", exist_ok=True)
    for i_face in sdd.interfaces:
        open(
            out_dir / "interface_contracts" / f"{i_face.name}.md",
            "w",
            encoding="utf-8",
        ).write(
            f"# {i_face.name}\n\nProducer: {i_face.producer}\nConsumer: {i_face.consumer}\n\nContract:\n{i_face.contract}\n"
        )
    assert (out_dir / "SDD.md").exists()
    assert (out_dir / "ImplementationPlan.md").exists()
    assert (out_dir / "bom.csv").exists()
    assert (out_dir / "budget.csv").exists()
    assert (out_dir / "interface_contracts" / "IF1.md").exists()
