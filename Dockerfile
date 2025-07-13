# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install uv: You can install uv globally in the image.
# uv can be installed via pip or directly from its releases.
# Installing via pip is generally straightforward.
RUN pip install uv

# Copy pyproject.toml and uv.lock (Crucial for reproducible builds)
# Copying these separately allows Docker to cache the 'uv sync' step
# as long as these files don't change.
COPY pyproject.toml uv.lock ./

# Install project dependencies using uv sync
# '--system' makes uv install into the system site-packages (or the venv it's in)
# '--prod' (or --no-dev) tells uv to only install production dependencies
RUN uv sync --system --prod

# Copy the rest of your application code
COPY . .

# Expose the port your application will listen on
EXPOSE 8080

# Cloud Run sets the PORT env var by default, but it's good practice for clarity
ENV PORT 8080

# Command to run your application using Gunicorn
# uv doesn't have a direct 'uv run' command for arbitrary scripts like Poetry.
# Instead, you activate the environment and then run your command.
# For simplicity, if uv installed directly into the system site-packages,
# you might not need an explicit activation if gunicorn is on the PATH.
# However, if uv creates a virtual environment, you'd activate it.
# A more robust way might be to add a simple shell script for startup.
# But generally, for simple cases where dependencies are in global site-packages:
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]

# Alternative if gunicorn isn't directly on PATH after uv sync
# (e.g., if uv created a venv in a non-standard location or for robustness)
# CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
