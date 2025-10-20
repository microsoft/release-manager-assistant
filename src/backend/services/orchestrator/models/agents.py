# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum


class Agent(Enum):
    """
    Enum for agent types used in the orchestrator.

    Attributes:
        JIRA_AGENT (str): Name of the JIRA agent.
        DEVOPS_AGENT (str): Name of the DevOps agent (DEPRECATED - database-based).
        AZURE_DEVOPS_AGENT (str): Name of the Azure DevOps agent (MCP-based).
        FINAL_ANSWER_GENERATOR_AGENT (str): Name of the Final Answer Generator agent.
        PLANNER_AGENT (str): Name of the Planner agent.
    """
    PLANNER_AGENT = "PLANNER_AGENT"
    JIRA_AGENT = "JIRA_AGENT"
    AZURE_DEVOPS_AGENT = "AZURE_DEVOPS_AGENT"
    FINAL_ANSWER_GENERATOR_AGENT = "FINAL_ANSWER_GENERATOR_AGENT"
    FALLBACK_AGENT = "FALLBACK_AGENT"