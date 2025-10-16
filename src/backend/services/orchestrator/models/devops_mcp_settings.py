# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class DevOpsMcpSettings:
    """
    Configuration settings for connecting to Azure DevOps via MCP (Model Context Protocol).

    This class holds the necessary connection parameters and configuration
    needed to establish and maintain a connection to Azure DevOps through the external MCP server.

    Attributes:
        azure_org_name (str): The Azure DevOps organization name (e.g., 'contoso').
        mcp_server_command (str, optional): Command to start the MCP server. Default is 'npx'.
        mcp_server_args (list, optional): Arguments for the MCP server command.
        mcp_timeout (int, optional): Timeout for MCP operations in seconds. Default is 30.
        max_retries (int, optional): Maximum number of retries for MCP operations. Default is 3.
        retry_delay (int, optional): Delay between retries in seconds. Default is 2.
        auto_start_server (bool, optional): Whether to automatically start the MCP server. Default is True.
        essential_tool_categories (dict, optional): Dictionary mapping category names to required patterns
            for validating essential Azure DevOps tools are available. Configurable to avoid hardcoding.
    """
    azure_org_name: str
    mcp_server_command: Optional[str] = "npx"
    mcp_server_args: Optional[List[str]] = None
    mcp_timeout: Optional[int] = 30
    max_retries: Optional[int] = 3
    retry_delay: Optional[int] = 2
    auto_start_server: Optional[bool] = True
    essential_tool_categories: Optional[Dict[str, List[str]]] = field(default_factory=lambda: {
        "core_projects": ["core", "list_projects"],
        "work_items": ["wit", "work"],
        "builds": ["build"],
        "repositories": ["repo", "pull_request"],
        "releases": ["release"]
    })

    def __post_init__(self):
        """
        Set default MCP server arguments if not provided.
        """
        if self.mcp_server_args is None:
            self.mcp_server_args = ["-y", "@azure-devops/mcp", self.azure_org_name]