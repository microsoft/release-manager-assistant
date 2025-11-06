# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from common.contracts.configuration.orchestrator_config import (
    ResolvedOrchestratorConfig,
)
from common.contracts.orchestrator.request import OrchestratorRequest
from common.telemetry.app_logger import AppLogger


async def get_orchestrator_runtime_config(logger: AppLogger, default_runtime_config) -> ResolvedOrchestratorConfig:
    """
    Fetches the orchestrator runtime configuration, applying overrides if available.

    Args:
        default_runtime_config: The default runtime configuration.
        caching_client: The caching client to fetch overrides from.
        request: The request containing potential overrides.
        logger: Logger for logging information and errors.

    Returns:
        ResolvedOrchestratorConfig: The resolved runtime configuration.
    """
    try:
        return ResolvedOrchestratorConfig(**default_runtime_config)

    except Exception as e:
        logger.error(f"Error fetching orchestrator runtime config: {e}")
        raise