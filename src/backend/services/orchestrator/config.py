# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
from dotenv import load_dotenv

from common.telemetry.app_logger import AppLogger
from common.telemetry.app_tracer_provider import AppTracerProvider
from common.utilities.config_reader import Config, ConfigReader


def str_to_bool(s: str):
    return s.lower() == "true"


# load value from .debug.env file if it exists, unless deploying in a production environment
if os.getenv("ENVIRONMENT") != "PROD":
    load_dotenv(override=True, dotenv_path=f"{os.getcwd()}/.env")


class DefaultConfig:
    _initialized = False

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            config_reader = ConfigReader(None)

            APPLICATION_INSIGHTS_CNX_STR = config_reader.read_config_value(Config.APPLICATION_INSIGHTS_CNX_STR)

            cls.tracer_provider = AppTracerProvider(APPLICATION_INSIGHTS_CNX_STR)
            cls.logger = AppLogger(APPLICATION_INSIGHTS_CNX_STR)
            cls.logger.set_base_properties({"ApplicationName": "ORCHESTRATOR_SERVICE"})
            config_reader.set_logger(cls.logger)

            try:
                cls.SERVICE_HOST = os.getenv(Config.SERVICE_HOST.value, "0.0.0.0")
                cls.SERVICE_PORT = int(os.getenv(Config.SERVICE_PORT.value, "5002"))

                cls.AGENT_ORCHESTRATOR_MAX_CONCURRENCY = int(os.getenv(Config.AGENT_ORCHESTRATOR_MAX_CONCURRENCY.value, "5"))

                cls.STORAGE_ACCOUNT_NAME = config_reader.read_config_value(Config.STORAGE_ACCOUNT_NAME)
                cls.VISUALIZATION_DATA_CONTAINER = config_reader.read_config_value(Config.VISUALIZATION_DATA_CONTAINER)

                cls.REDIS_HOST = config_reader.read_config_value(Config.REDIS_HOST)
                cls.REDIS_PORT = config_reader.read_config_value(Config.REDIS_PORT)
                cls.REDIS_PASSWORD = config_reader.read_config_value(Config.REDIS_PASSWORD)

                cls.REDIS_TASK_QUEUE_CHANNEL = config_reader.read_config_value(Config.REDIS_TASK_QUEUE_CHANNEL)
                cls.REDIS_MESSAGE_QUEUE_CHANNEL = config_reader.read_config_value(Config.REDIS_MESSAGE_QUEUE_CHANNEL)

                # JIRA configuration
                cls.USE_JIRA_MCP_SERVER = str_to_bool(os.getenv(Config.USE_JIRA_MCP_SERVER.value, "true"))
                cls.JIRA_SERVER_ENDPOINT = config_reader.read_config_value(Config.JIRA_SERVER_ENDPOINT)

                # Only read these values if not using the hosted JIRA MCP server
                cls.JIRA_SERVER_USERNAME = config_reader.read_config_value(Config.JIRA_SERVER_USERNAME) if not cls.USE_JIRA_MCP_SERVER else None
                cls.JIRA_SERVER_PASSWORD = config_reader.read_config_value(Config.JIRA_SERVER_PASSWORD) if not cls.USE_JIRA_MCP_SERVER else None

                cls.AZURE_DEVOPS_ORG_NAME = config_reader.read_config_value(Config.AZURE_DEVOPS_ORG_NAME)
                cls.AZURE_DEVOPS_EXT_PAT = config_reader.read_config_value(Config.AZURE_DEVOPS_EXT_PAT)

                cls.AZURE_AI_PROJECT_ENDPOINT = config_reader.read_config_value(Config.AZURE_AI_PROJECT_ENDPOINT)
                cls.AZURE_AI_MODEL_DEPLOYMENT_NAME = config_reader.read_config_value(Config.AZURE_AI_MODEL_DEPLOYMENT_NAME)

                cls._initialized = True

            except Exception as e:
                cls.logger.error(f"Error while loading config: {e}")
                raise e
