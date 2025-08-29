import warnings

from core.agents.documentation_agent import DocumentationAgent
from core.agents.data_scientist_analytics_engineer_agent import (
    DataScientistAnalyticsEngineerAgent,
)
from core.agents.fluorescence_biological_sample_expert_agent import (
    FluorescenceBiologicalSampleExpertAgent,
)


def _assert_single_warning(agent_cls, expected):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        agent_cls("gpt-4o-mini")
        agent_cls("gpt-4o-mini")
    msgs = [str(m.message) for m in w if m.category is DeprecationWarning]
    assert len(msgs) == 1
    assert expected in msgs[0]


def test_legacy_agents_emit_warning_once():
    _assert_single_warning(DocumentationAgent, "documentation.v1")
    _assert_single_warning(
        DataScientistAnalyticsEngineerAgent,
        "data_scientist_analytics_engineer.v1",
    )
    _assert_single_warning(
        FluorescenceBiologicalSampleExpertAgent,
        "fluorescence_biological_sample_expert.v1",
    )
