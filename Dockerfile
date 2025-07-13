# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv (modern Python package manager)
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Run the application
CMD ["python", "main.py"]
