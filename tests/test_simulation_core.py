from dr_rd.simulation import sim_core
from dr_rd.simulation.interfaces import SimulationSpec
from dr_rd.simulation.mechanical import MechanicalSimulator
from dr_rd.simulation.materials import MaterialsSimulator
from dr_rd.simulation.finance import FinanceSimulator


def test_registration_and_run_mechanical():
    sim_core.register("mechanical", MechanicalSimulator())
    spec = SimulationSpec(id="1", domain="mechanical", inputs={"length": 1, "width": 1, "height": 1, "density": 1, "load": 1})
    res = sim_core.run("mechanical", spec, {})
    assert res.ok and res.metrics["mass"] == 1


def test_run_materials_and_finance():
    sim_core.register("materials", MaterialsSimulator())
    sim_core.register("finance", FinanceSimulator())
    spec_m = SimulationSpec(id="2", domain="materials", inputs={"query": "steel"})
    res_m = sim_core.run("materials", spec_m, {})
    assert "Steel" in res_m.findings
    spec_f = SimulationSpec(id="3", domain="finance", inputs={"cash_flows": [1.0], "discount_rate": 0.1})
    res_f = sim_core.run("finance", spec_f, {})
    assert round(res_f.metrics["npv"], 5) == 0.90909
