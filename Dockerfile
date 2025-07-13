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
RUN uv sync --frozen

# Copy the rest of your application code
COPY . .

# Expose the port your application will listen on
EXPOSE 8080

# Cloud Run sets the PORT env var by default, but it's good practice for clarity
ENV PORT 8080
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Run the application
CMD ["python", "main.py"]

# Command to run your application using Gunicorn
# uv doesn't have a direct 'uv run' command for arbitrary scripts like Poetry.
# Instead, you activate the environment and then run your command.
# For simplicity, if uv installed directly into the system site-packages,
# you might not need an explicit activation if gunicorn is on the PATH.
# However, if uv creates a virtual environment, you'd activate it.
# A more robust way might be to add a simple shell script for startup.
# But generally, for simple cases where dependencies are in global site-packages:
# CMD ["/bin/bash", "-c", "source .venv/bin/activate && gunicorn --bind 0.0.0.0:8080 main:app"]

# Alternative using 'python -m' which can sometimes automatically find the venv
# This often works because uv typically puts the venv's python in a common location.
# CMD ["/app/.venv/bin/python", "-m", "gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
