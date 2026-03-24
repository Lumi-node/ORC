FROM python:3.12-slim

WORKDIR /app

# Install the package
COPY . .
RUN pip install --no-cache-dir -e ".[dev]"

# Run the quick battle example
CMD ["python", "examples/quick_battle.py"]
