# Use a smaller base image
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y build-essential

# Set working directory
WORKDIR /code

# Copy and install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Final stage
FROM python:3.9-slim

# Set working directory
WORKDIR /code

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ./app /code/app

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]