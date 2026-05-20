from fastapi import FastAPI
from datetime import datetime
import os
import time

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

resource = Resource.create({
    "service.name": "llm-app",
    "deployment.environment": os.getenv("ENVIRONMENT", "dev")
})

trace.set_tracer_provider(TracerProvider(resource=resource))

otlp_endpoint = os.getenv(
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    "http://otel-collector:4318/v1/traces"
)

span_processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint=otlp_endpoint)
)

trace.get_tracer_provider().add_span_processor(span_processor)

tracer = trace.get_tracer(__name__)

app = FastAPI(title="AI Observability Demo App")


@app.get("/")
def home():
    with tracer.start_as_current_span("home_request") as span:
        span.set_attribute("app.route", "/")
        span.set_attribute("llm.service", "demo-ai-observability-app")

        return {
            "message": "AI Observability App is running on AKS",
            "service": "llm-app",
            "environment": os.getenv("ENVIRONMENT", "dev"),
            "time": datetime.utcnow().isoformat()
        }


@app.get("/ask")
def ask(prompt: str = "Explain AI observability"):
    with tracer.start_as_current_span("llm_request") as span:
        start = time.time()

        demo_response = f"This is a demo AI response for: {prompt}"
        latency_ms = round((time.time() - start) * 1000, 2)

        span.set_attribute("llm.prompt", prompt)
        span.set_attribute("llm.response", demo_response)
        span.set_attribute("llm.model", "demo-model")
        span.set_attribute("llm.provider", "demo")
        span.set_attribute("llm.latency_ms", latency_ms)
        span.set_attribute("ai.governance.pii_checked", True)

        return {
            "prompt": prompt,
            "response": demo_response,
            "model": "demo-model",
            "observability": {
                "tracing": "OpenTelemetry enabled",
                "collector": otlp_endpoint,
                "backend": "OTEL Collector debug exporter"
            }
        }


@app.get("/health")
def health():
    with tracer.start_as_current_span("health_check") as span:
        span.set_attribute("app.route", "/health")
        return {"status": "healthy"}