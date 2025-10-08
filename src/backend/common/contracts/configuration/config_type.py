# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum

class ConfigType(Enum):
    AGENT = "agent"
    SERVICE = "service"
    SYSTEM = "system"
    EVALUATION = "evaluation"
    ORCHESTRATOR = "orchestrator"

    @classmethod
    def get_model(cls, config_type: str):
        # Import here to avoid circular imports
        from common.contracts.configuration.agent_config import AgentConfig
        from common.contracts.configuration.service_config import ServiceConfig
        from common.contracts.configuration.system_config import SystemConfig
        from common.contracts.configuration.orchestrator_config import OrchestratorServiceConfig

        config_type_to_model = {
            cls.AGENT.value: AgentConfig,
            cls.SERVICE.value: ServiceConfig,
            cls.SYSTEM.value: SystemConfig,
            cls.ORCHESTRATOR.value: OrchestratorServiceConfig,
        }

        try:
            return config_type_to_model[config_type]
        except KeyError:
            raise ValueError(f"Unknown config type: {config_type}")