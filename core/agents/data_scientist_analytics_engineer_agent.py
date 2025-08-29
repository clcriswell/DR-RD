from core.agents.base_agent import BaseAgent
from core.compat.deprecations import warn_legacy_agent_use

"""Data Scientist / Analytics Engineer Agent."""

class DataScientistAnalyticsEngineerAgent(BaseAgent):
    """Agent that provides data strategy and analytics modeling for the project."""

    def __init__(self, model):
        warn_legacy_agent_use(
            "Data Scientist / Analytics Engineer",
            "data_scientist_analytics_engineer.v1",
            "2025-12-31",
        )
        super().__init__(
            name="Data Scientist / Analytics Engineer",
            model=model,
            system_message=(
                # Schema: dr_rd/schemas/data_scientist_analytics_engineer_agent.json
                "You are a data scientist and analytics engineer who excels in handling large datasets "
                "and extracting insights. You design data collection strategies and build models "
                "(statistical or ML) to analyze experimental results or predict outcomes. "
                "You consider data pipeline design, from acquisition and cleaning to visualization and "
                "deployment of analytical tools."
            ),
            user_prompt_template=(
                # Schema: dr_rd/schemas/data_scientist_analytics_engineer_agent.json
                "Project Idea: {idea}\n"
                "As the Data Scientist / Analytics Engineer, your task is {task}. "
                "Provide a detailed data and analytics plan in Markdown, including what data will be "
                "collected during the project, how it will be stored and processed, and what analysis "
                "or machine learning models will be applied. Outline any predictive modeling or statistical "
                "analysis to be done (for example, using AutoML or custom models) and how the results will "
                "be validated. Also describe how insights will be delivered (dashboards, reports, etc.). "
                "Conclude with a JSON list of data sources and planned analysis/modeling techniques."
            ),
        )
