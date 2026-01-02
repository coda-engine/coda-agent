from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def setup_telemetry(app):
    """
    Sets up OpenTelemetry instrumentation for the FastAPI application.
    """
    try:
        endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
        # Ensure standard OTLP HTTP path if generic endpoint given
        if not endpoint.endswith("/v1/traces"):
            endpoint = f"{endpoint}/v1/traces"

        logger.info(f"Setting up OpenTelemetry with endpoint: {endpoint}")

        resource = Resource(attributes={
            SERVICE_NAME: settings.OTEL_SERVICE_NAME
        })
        
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        
        otel_exporter = OTLPSpanExporter(endpoint=endpoint)
        span_processor = BatchSpanProcessor(otel_exporter)
        provider.add_span_processor(span_processor)
        
        # Auto-instrument FastAPI
        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
        
        # Prometheus Metrics
        Instrumentator().instrument(app).expose(app)
        
        logger.info("OpenTelemetry setup complete.")
        return provider
    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry: {e}")
        return None
