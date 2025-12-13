FROM python:3.11-slim

LABEL org.opencontainers.image.title="Stacks PoX Exporter"
LABEL org.opencontainers.image.description="Prometheus exporter for Stacks PoX cycle monitoring"
LABEL org.opencontainers.image.source="https://github.com/your-org/stacks-monitoring"

WORKDIR /app

COPY pox-exporter.py .

# Default port
EXPOSE 9816

# Run as non-root user
RUN useradd -r -s /bin/false exporter
USER exporter

CMD ["python3", "pox-exporter.py"]
