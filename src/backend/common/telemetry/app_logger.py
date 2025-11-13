# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import logging
from enum import Enum
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry._logs import set_logger_provider


from common.telemetry.log_classes import LogProperties

DEFAULT_RESOURCE = Resource.create({"resource.name": "telemetry"})

class LogEvent(Enum):
    REQUEST_RECEIVED = "Request.Received"
    REQUEST_SUCCESS = "Request.Success"
    REQUEST_FAILED = "Request.Failed"

class ConsoleLogFilter(logging.Filter):
    '''
    Since we are using root logger, in console we see all the logs from all the modules.
    This filter will filter out logs that are not from our app and reduce verbosity from third-party libraries.
    '''
    def __init__(self):
        super().__init__()
        self.base_dir = os.path.abspath(os.path.join(__file__, "..", ".."))

        # Define allowed third-party loggers (only show WARNING and above)
        self.allowed_third_party = [
            "semantic_kernel",
            "agent_framework",
            "azure_mcp"
        ]

    def filter(self, record):
        # Always allow logs from our application
        if os.path.abspath(record.pathname).startswith(self.base_dir):
            return True

        # For third-party libraries, only show WARNING and above to reduce noise
        for allowed in self.allowed_third_party:
            if record.name.startswith(allowed):
                return record.levelno >= logging.WARNING

        # Filter out everything else
        return False

class AppLogger:
    def __init__(self, connection_string: str = None, logger: logging.Logger = None, resource: Resource = None):
        """
        Initialize AppLogger with either a connection string or an existing logger.

        Args:
            connection_string: Azure Monitor connection string for telemetry (optional if logger is provided)
            logger: Existing logger instance to wrap (optional if connection_string is provided)
            resource: Resource describing the service (optional)
        """
        if logger is not None:
            # Initialize from existing logger
            self.connection_string = connection_string
            self.logger = logger
            self.logger_provider = LoggerProvider(resource or DEFAULT_RESOURCE)
            self._from_existing_logger = True

            self.logger.setLevel(logging.INFO)

            # Set up third-party logger levels
            logging.getLogger("azure.identity").setLevel(logging.WARNING)
            logging.getLogger("azure.core.pipeline.policies").setLevel(logging.WARNING)
            logging.getLogger("azure.monitor.opentelemetry.exporter.export").setLevel(logging.WARNING)

            # Only initialize Azure Monitor if connection string is provided
            if connection_string:
                self.initialize_loggers()
        else:
            # Original initialization path
            if connection_string is None:
                raise ValueError("Either connection_string or logger must be provided")

            self.connection_string = connection_string
            self._from_existing_logger = False

            logging.getLogger("azure.identity").setLevel(logging.WARNING)
            logging.getLogger("azure.core.pipeline.policies").setLevel(logging.WARNING)
            logging.getLogger("azure.monitor.opentelemetry.exporter.export").setLevel(logging.WARNING)

            self.logger = logging.getLogger()
            self.logger.setLevel(logging.INFO)
            self.logger_provider = LoggerProvider(resource)

            self.initialize_loggers()

    @classmethod
    def from_logger(cls, logger: logging.Logger, connection_string: str = None, resource: Resource = None) -> "AppLogger":
        """
        Create an AppLogger instance from an existing logger.

        Args:
            logger: Existing logger instance to wrap
            connection_string: Optional Azure Monitor connection string for telemetry

        Returns:
            AppLogger instance that wraps the provided logger
        """
        return cls(connection_string=connection_string, logger=logger, resource=resource)

    def initialize_loggers(self):
        if self.connection_string:
            if not any(
                isinstance(handler, LoggingHandler)
                for handler in self.logger.handlers
            ):
                self.azure_exporter = AzureMonitorLogExporter(connection_string=self.connection_string)
                self.logger_provider.add_log_record_processor(BatchLogRecordProcessor(self.azure_exporter))
                self.handler = LoggingHandler()
                self.logger.addHandler(self.handler)

        # Only add console handler if we're not using an existing logger or if no StreamHandler exists
        if not any(
            isinstance(handler, logging.StreamHandler)
            for handler in self.logger.handlers
        ):
            console_handler = logging.StreamHandler()
            # Make console log level configurable via environment variable
            console_log_level = os.getenv('CONSOLE_LOG_LEVEL', 'INFO').upper()
            log_level = getattr(logging, console_log_level, logging.INFO)
            console_handler.setLevel(log_level)
            console_handler.addFilter(ConsoleLogFilter())
            self.logger.addHandler(console_handler)

        if not self._from_existing_logger:
            set_logger_provider(self.logger_provider)

    def info(self, message:str, properties: dict = None):
        self.logger.info(message)

    # Put this function for now, but if we decide to go with this approach, we can delete this function
    # TODO: Remove set_base_properties function here and through code.
    def set_base_properties(self, base_properties: dict | LogProperties):
        pass

    def debug(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        self.logger.info(msg)

    def warning(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        self.logger.warning(msg)

    def error(self, msg: str, event: LogEvent = None, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        self.logger.error(msg)

    def exception(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        self.logger.exception(msg)

    def critical(self, msg: str, properties: dict = None):
        """
        Log a message by merging additional properties into custom dimensions
        """
        self.logger.critical(msg)

    def log_request_received(self, msg: str, properties: LogProperties = None):
        self.info(msg)

    def log_request_success(self, msg: str, properties: LogProperties = None):
        self.info(msg)

    def log_request_failed(self, msg: str, properties: LogProperties = None):
        self.error(msg)