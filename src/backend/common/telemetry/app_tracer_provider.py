# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional
import time
from datetime import datetime, timezone

import logging
from contextlib import contextmanager

from more_itertools import extract
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import SpanKind
from opentelemetry.trace import set_tracer_provider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.propagate import inject, extract
from opentelemetry.context.context import Context

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

logger = logging.getLogger(__name__)

class AppTracerProvider:
    """
    Provides tracing capabilities for the application.

    This class wraps OpenTelemetry's tracing functionality and provides a more
    user-friendly API for injecting and extracting trace context.

    Call `initialize()` to set up the tracer provider.
    """
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

        self.tracer = None
        self.enabled = False

    def initialize(self):
        try:
            # Create resource with evaluation-specific attributes
            resource = Resource.create({
                "service.name": "ReleaseManagerAssistant",
                "service.version": "1.0.0",
                "service.namespace": "rma-template"
            })

            tracer_provider = TracerProvider(resource=resource)

            exporter = AzureMonitorTraceExporter(connection_string=self.connection_string)
            tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
            set_tracer_provider(tracer_provider)

            self.tracer = trace.get_tracer("release-manager-assistant")
            self.enabled = True

        except Exception as ex:
            logger.error(
                f"Failed to initialize Application Insights telemetry: {ex}")
            self.enabled = False

    def inject_trace_context(self, trace_context: dict) -> None:
        """
        Injects tracing context into the provided dictionary for distributed tracing.
        This is a wrapper around OpenTelemetry's inject function that provides
        a more descriptive API for our services.

        Args:
            trace_context: Dictionary to inject the tracing context into.
        """
        inject(trace_context)

    def extract_trace_context(self, trace_context: dict) -> Context:
        """
        Extracts tracing context from a carrier dictionary and attaches it to the current context.
        This combines extraction and attachment in one operation to ensure proper context propagation.

        Args:
            trace_context: Dictionary containing the tracing context to extract.
        """
        return extract(trace_context)

    @contextmanager
    def trace_session(self, session_id: str, request_path: Optional[str] = None):
        """
        Creates a tracing span for a session.

        Args:
            session_id: The ID of the session to trace.
            request_path [Optional]: The path of the request being traced.
        """
        if not self.enabled or not self.tracer:
            yield None
            return

        with self.tracer.start_as_current_span(
            name=f"session_{session_id}",
            kind=SpanKind.SERVER,
            attributes={
                "request.path": request_path,
                "request.timestamp": datetime.now(timezone.utc).isoformat()
            }
        ) as span:
            start_time = time.monotonic()
            try:
                yield span

                # Record successful request processing event
                duration = time.monotonic() - start_time
                span.set_attribute("request.duration", duration)
                span.set_status(Status(StatusCode.OK))
            except Exception as ex:
                # Record failed request processing event
                duration = time.monotonic() - start_time
                span.set_status(Status(StatusCode.ERROR, str(ex)))
                span.record_exception(ex)
                raise
    
    @contextmanager
    def trace_message_enqueue(
        self,
        session_id: str,
        message_type: str,
        message_queue_name: str,
        context: Optional[Context] = None
    ):
        """
        Creates a tracing span for a message enqueue operation.

        Args:
            session_id: The ID of the session to trace.
            message_type: The type of the message being enqueued.
            message_queue_name: The name of the message queue.
        """
        if not self.enabled or not self.tracer:
            yield None
            return

        with self.tracer.start_as_current_span(
            name=f"message_enqueue_{message_type}",
            kind=SpanKind.PRODUCER,
            attributes={
                "message.session_id": session_id,
                "message.type": message_type,
                "message.queue": message_queue_name,
                "message.timestamp": datetime.now(timezone.utc).isoformat()
            },
            context=context
        ) as span:
            start_time = time.monotonic()
            try:
                yield span

                # Record successful message enqueueing event
                duration = time.monotonic() - start_time
                span.set_attribute("message.duration", duration)
                span.set_status(Status(StatusCode.OK))
            except Exception as ex:
                # Record failed message enqueueing event
                duration = time.monotonic() - start_time
                span.set_status(Status(StatusCode.ERROR, str(ex)))
                span.record_exception(ex)
                raise
    
    @contextmanager
    def trace_message_dequeue(
        self,
        session_id: str,
        message_type: str,
        message_queue_name: str,
        context: Optional[Context] = None
    ):
        """
        Creates a tracing span for a message dequeue operation.

        Args:
            session_id: The ID of the session to trace.
            message_type: The type of the message being dequeued.
            message_queue_name: The name of the message queue.
        """
        if not self.enabled or not self.tracer:
            yield None
            return

        with self.tracer.start_as_current_span(
            name=f"message_dequeue_{message_type}",
            kind=SpanKind.CONSUMER,
            attributes={
                "message.session_id": session_id,
                "message.type": message_type,
                "message.queue": message_queue_name,
                "message.timestamp": datetime.now(timezone.utc).isoformat()
            },
            context=context
        ) as span:
            start_time = time.monotonic()
            try:
                yield span

                # Record successful message enqueueing event
                duration = time.monotonic() - start_time
                span.set_attribute("message.duration", duration)
                span.set_status(Status(StatusCode.OK))
            except Exception as ex:
                # Record failed message enqueueing event
                duration = time.monotonic() - start_time
                span.set_status(Status(StatusCode.ERROR, str(ex)))
                span.record_exception(ex)
                raise

    @contextmanager
    def trace_agent_orchestration(
        self,
        session_id: str,
        context: Optional[Context] = None
    ):
        """
        Creates a tracing span for agent orchestration.

        Args:
            session_id: The ID of the session to trace.
            context: The tracer context extracted from request for distributed tracing.
        """
        if not self.enabled or not self.tracer:
            yield None
            return

        with self.tracer.start_as_current_span(
            name=f"agent_orchestration_{session_id}",
            kind=SpanKind.CONSUMER,
            attributes={
                "orchestrator.request.session_id": session_id,
                "orchestrator.request.timestamp": datetime.now(timezone.utc).isoformat()
            },
            context=context
        ) as span:
            start_time = time.monotonic()
            try:
                yield span

                # Record successful agent orchestration event
                duration = time.monotonic() - start_time
                span.set_attribute("orchestrator.duration", duration)
                span.set_status(Status(StatusCode.OK))
            except Exception as ex:
                # Record failed agent orchestration event
                duration = time.monotonic() - start_time
                span.set_status(Status(StatusCode.ERROR, str(ex)))
                span.record_exception(ex)
                raise

    @contextmanager
    def trace_agent_run(
        self,
        session_id: str,
        agent_name: str,
        context: Optional[Context] = None
    ):
        """
        Creates a tracing span for agent run.

        Args:
            session_id: The ID of the session to trace.
            agent_name: The name of the agent being run.
        """
        if not self.enabled or not self.tracer:
            yield None
            return

        with self.tracer.start_as_current_span(
            name=f"agent_{agent_name}",
            kind=SpanKind.CLIENT,
            attributes={
                "agent.run.session_id": session_id,
                "agent.run.name": agent_name,
                "agent.run.timestamp": datetime.now(timezone.utc).isoformat()
            },
            context=context
        ) as span:
            start_time = time.monotonic()
            try:
                yield span

                # Record successful agent run event
                duration = time.monotonic() - start_time
                span.set_attribute("agent.run.duration", duration)
                span.set_status(Status(StatusCode.OK))
            except Exception as ex:
                # Record failed agent run event
                duration = time.monotonic() - start_time
                span.set_status(Status(StatusCode.ERROR, str(ex)))
                span.record_exception(ex)
                raise