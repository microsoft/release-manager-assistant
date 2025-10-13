# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional
from dataclasses import dataclass


@dataclass
class JiraSettings:
    """
    Configuration settings for connecting to a Jira server.

    This class holds the necessary credentials and connection information
    needed to authenticate and interact with a Jira instance.

    Attributes:
        server_url (str): The URL of the Jira server.
        username (str): The username for Jira authentication.
        password (str): The password for Jira authentication.
        config_file_path (str): The file path for the configuration file containing additional metadata.
    """
    server_url: str
    use_mcp_server: bool
    username: Optional[str] = None
    password: Optional[str] = None
    config_file_path: Optional[str] = None
