# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pydantic import BaseModel
from typing import Any, Dict, Optional


class OrchestratorRequest(BaseModel):
    """
    Represents a request to the orchestrator, containing user input and context information.

    Attributes:
        session_id (str): Unique identifier for the session.
        dialog_id (str): Unique identifier for the dialog.
        user_id (str): Identifier for the user, defaults to "anonymous".
        message (str): The user message.
        authorization (Optional[str]): Optional authorization token for the request.
        locale (Optional[str]): Locale of the user query, if specified.
        user_profile (Optional[UserProfile]): Optional user profile information.
        additional_metadata (Dict[str, Any]): Additional metadata for the request.
    """
    session_id: str
    dialog_id: str
    user_id: str = "anonymous"
    message: str
    authorization: Optional[str] = None
    locale: Optional[str] = None
    # The following fields are optional and can be used for additional metadata specific to the use-case.
    # They can be set to None if not needed.
    additional_metadata: Dict[str, Any] | None = None
