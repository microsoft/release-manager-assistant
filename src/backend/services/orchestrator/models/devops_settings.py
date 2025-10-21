# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional
from dataclasses import dataclass

from plugins.az_devops_plugin import AzDevOpsPluginFactory


@dataclass
class DevOpsSettings:
    """
    Configuration settings for connecting to Azure DevOps.

    Attributes:
        use_mcp_server (bool): Whether to connect via an MCP server.
        mcp_server_endpoint (str, optional): The endpoint URL of the MCP server if used.
        mcp_plugin_factory (AzDevOpsPluginFactory, optional): Pre-initialized MCP plugin factory.
    """
    use_mcp_server: bool = False
    mcp_server_endpoint: Optional[str] = None
    mcp_plugin_factory: Optional[AzDevOpsPluginFactory] = None