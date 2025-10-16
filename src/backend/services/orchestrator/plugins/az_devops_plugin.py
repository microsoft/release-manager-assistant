"""
Azure DevOps MCP Plugin for Semantic Kernel

Creates and manages Azure DevOps MCP server connections for Semantic Kernel.
Handles authentication, tool discovery, and memory hydration automatically.

Prerequisites:
- Azure CLI authentication (run 'az login') OR set AZURE_DEVOPS_EXT_PAT environment variable
- Node.js and npm installed (for the MCP server)
"""
import os
import json
import subprocess
import shutil
from dataclasses import dataclass
from typing import List, Dict, Any

from agent_framework import MCPStdioTool, AIFunction

from models.devops_mcp_settings import DevOpsMcpSettings
from common.telemetry.app_logger import AppLogger


class AzDevOpsPluginInitializationError(Exception):
    """Raised when plugin initialization fails."""
    pass


class AzDevOpsAuthenticationError(AzDevOpsPluginInitializationError):
    """Raised when Azure DevOps authentication fails."""
    pass


class ToolValidationError(AzDevOpsPluginInitializationError):
    """Raised when required tools are missing."""
    pass


@dataclass
class AzureDevOpsPluginStatus:
    """Health status report for an initialized Azure DevOps plugin."""
    tools_available: int          # Number of tools discovered
    missing_categories: List[str]  # Essential tool categories not found
    warnings: List[str]           # Non-fatal issues during initialization

class AzDevOpsPluginFactory:
    """Creates and configures Azure DevOps MCP plugins with proper lifecycle management."""

    def __init__(self, logger: AppLogger):
        self.logger = logger
        self._plugin = None

    @property
    def plugin(self) -> MCPStdioTool:
        """Get the current plugin instance."""
        if self._plugin is None:
            raise AzDevOpsPluginInitializationError("Plugin not initialized. Call create_plugin() first.")
        return self._plugin

    @property
    def is_initialized(self) -> bool:
        """Check if the plugin has been successfully initialized."""
        return self._plugin is not None

    async def create_plugin(
        self,
        devops_settings: DevOpsMcpSettings,
        plugin_name: str = "DevOpsPlugin"
    ) -> tuple[MCPStdioTool, AzureDevOpsPluginStatus]:
        """Create and configure an Azure DevOps MCP plugin.

        Args:
            devops_settings: Azure DevOps configuration and settings
            plugin_name: Display name for the plugin

        Returns:
            Tuple of (ready-to-use plugin, health status report)

        Raises:
            AuthenticationError: Azure DevOps authentication failed
            ToolValidationError: Required tools are missing
            PluginInitializationError: Other initialization failures
        """
        try:
            # Validate configuration first
            self.__validate_settings(devops_settings)

            # Test Azure DevOps authentication
            # await self.__validate_authentication()

            # Create the MCP plugin instance
            self._plugin = await self.__create_mcp_plugin(devops_settings, plugin_name)

            # Discover available tools from the server
            functions = await self.__discover_tools()

            # Check if essential tool categories are present
            missing_categories = self.__validate_tool_categories(
                functions, devops_settings.essential_tool_categories
            )

            # Build comprehensive health report
            warnings = []
            if missing_categories:
                warnings.append(f"Missing tool categories: {missing_categories}")

            # Note: Some MCP servers load tools lazily during first use
            if not functions:
                warnings.append("No tools discovered during initialization - they may load on first use")

            health = AzureDevOpsPluginStatus(
                tools_available=len(functions),
                missing_categories=missing_categories,
                warnings=warnings
            )

            # Log success with helpful details
            if functions:
                self.logger.info(f"Plugin '{plugin_name}' ready with {len(functions)} tools")
            else:
                self.logger.info(f"Plugin '{plugin_name}' ready (tools will load on demand)")

            return self._plugin, health
        except Exception as e:
            self.logger.error(f"Plugin initialization failed: {e}")
            raise


    async def cleanup(self):
        """
        Clean up resources, especially the MCP plugin.
        """
        if self._plugin:
            await self._plugin.close()

        self._plugin = None

    def __validate_settings(self, settings: DevOpsMcpSettings) -> None:
        """Validate required settings are present and have valid values."""
        # Check for required configuration fields
        required_fields = ['azure_org_name', 'mcp_server_command', 'mcp_server_args']
        missing = [field for field in required_fields if not getattr(settings, field, None)]
        if missing:
            raise AzDevOpsPluginInitializationError(f"Missing required settings: {missing}")

        # Validate string fields aren't empty
        if not settings.azure_org_name.strip():
            raise AzDevOpsPluginInitializationError("Organization name cannot be empty")

        if settings.mcp_server_command and not settings.mcp_server_command.strip():
            raise AzDevOpsPluginInitializationError("MCP server command cannot be empty")

        # Validate numeric settings have reasonable values
        if settings.mcp_timeout is not None and settings.mcp_timeout <= 0:
            raise AzDevOpsPluginInitializationError(f"Invalid timeout value: {settings.mcp_timeout}")

        if settings.max_retries is not None and settings.max_retries < 0:
            raise AzDevOpsPluginInitializationError(f"Invalid max_retries value: {settings.max_retries}")

        if settings.retry_delay is not None and settings.retry_delay < 0:
            raise AzDevOpsPluginInitializationError(f"Invalid retry_delay value: {settings.retry_delay}")


    async def __validate_authentication(self) -> None:
        """Verify Azure CLI is installed and authenticated."""
        try:
            # Find Azure CLI executable
            az_cmd = shutil.which("az")

            # Try common Windows installation paths if not in PATH
            if not az_cmd:
                common_paths = [
                    r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
                    r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        az_cmd = path
                        break

            if not az_cmd:
                raise RuntimeError("Azure CLI is not installed or not accessible")

            # Check if Azure CLI is working
            result = subprocess.run(
                [az_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError("Azure CLI is not installed or not accessible")

            # Check if user is authenticated
            result = subprocess.run(
                [az_cmd, "account", "show"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError("Azure CLI is not authenticated. Please run 'az login'")

            # Log authentication details for debugging
            account_info = json.loads(result.stdout)
            tenant_id = account_info.get("tenantId")
            user_name = account_info.get("user", {}).get("name", "Unknown")

            self.logger.info(f"Azure CLI authenticated as: {user_name} (Tenant: {tenant_id})")
        except subprocess.TimeoutExpired:
            raise AzDevOpsAuthenticationError("Azure CLI command timed out")
        except json.JSONDecodeError:
            raise AzDevOpsAuthenticationError("Failed to parse Azure CLI response")
        except FileNotFoundError:
            raise AzDevOpsAuthenticationError("Azure CLI is not installed")
        except Exception as e:
            self.logger.error(f"Authentication validation failed: {e}")
            raise AzDevOpsAuthenticationError("Azure DevOps authentication failed") from e

    async def __create_mcp_plugin(
        self,
        settings: DevOpsMcpSettings,
        plugin_name: str
    ) -> MCPStdioTool:
        """Create the MCP plugin with secure environment setup."""
        try:
            plugin = MCPStdioTool(
                name=plugin_name,
                description=f"Azure DevOps MCP tools for org '{settings.azure_org_name}'",
                command=settings.mcp_server_command,
                args=settings.mcp_server_args,
                request_timeout=settings.mcp_timeout or 60  # Default 60 seconds
            )

            return plugin
        except Exception as e:
            raise AzDevOpsPluginInitializationError(f"Failed to start MCP server: {e}") from e


    async def __discover_tools(self) -> List[AIFunction[Any, Any]]:
        """Connect to MCP server and discover available tools."""
        if self._plugin is None:
            raise AzDevOpsPluginInitializationError("Plugin not initialized")

        try:
            # Connect to the server and load all available tools
            await self._plugin.connect()
            await self._plugin.load_tools()

            # Some servers return None instead of empty list
            if self._plugin.functions is None:
                self.logger.info("Tools not available during discovery - they may load on demand")
                return []

            self.logger.info(f"Discovered {len(self._plugin.functions)} MCP tools")
            return self._plugin.functions
        except Exception as e:
            self.logger.warning(f"Tool discovery failed: {e}")
            return []


    def __validate_tool_categories(
        self,
        functions: List[AIFunction[Any, Any]],
        essential_categories: Dict[str, List[str]]
    ) -> List[str]:
        """Check if essential tool categories are available."""

        if not essential_categories:
            return []

        # Skip validation if no tools found (they may load lazily)
        if not functions:
            self.logger.info("No tools discovered - skipping category validation (tools may load on demand)")
            return []

        # Check which essential categories are missing
        names = [f.name.lower() for f in functions]
        missing = []

        for category, patterns in essential_categories.items():
            if not any(all(pat in name for pat in patterns) for name in names):
                missing.append(category)

        if missing:
            self.logger.warning(f"Missing essential tool categories: {missing}")
        else:
            self.logger.info("All essential tool categories are available")

        return missing
