# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

class MCPServerConfig(BaseSettings):
    """MCP Server configuration."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # ignore extra environment variables
    )

    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=12321)
    debug: bool = Field(default=False)

    # MCP specific settings
    server_name: str = Field()


# Global configuration instance
config = MCPServerConfig()


def get_server_config():
    """Get server configuration."""
    return {
        "host": config.host,
        "port": config.port,
        "debug": config.debug
    }
