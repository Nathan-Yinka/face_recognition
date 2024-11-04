# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies with verbose output
RUN apt-get update -y && \
    apt-get install -y cmake build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install Python dependencies with verbose logging
RUN pip install --no-cache-dir -r requirements.txt -vvv

# Copy the rest of the application code
COPY . /app/

# Set environment variables to avoid Python buffering and set Django settings
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

# Run migrations and collect static files (with verbose output)
RUN python manage.py collectstatic --noinput --verbosity 3
RUN python manage.py migrate --verbosity 3

# Expose port 8000 to the outside world
EXPOSE 8000

# Start the Django application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application", "--log-level", "debug"]
