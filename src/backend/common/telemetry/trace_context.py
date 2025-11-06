# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from opentelemetry.propagate import inject, extract
from opentelemetry.context.context import Context

def inject_trace_context(trace_context: dict) -> None:
    """
    Injects tracing context into the provided dictionary for distributed tracing.
    This is a wrapper around OpenTelemetry's inject function that provides
    a more descriptive API for our services.

    Args:
        trace_context: Dictionary to inject the tracing context into.
    """
    inject(trace_context)

def extract_trace_context(trace_context: dict) -> Context:
    """
    Extracts tracing context from a carrier dictionary and attaches it to the current context.
    This combines extraction and attachment in one operation to ensure proper context propagation.

    Args:
        trace_context: Dictionary containing the tracing context to extract.
    """
    return extract(trace_context)
