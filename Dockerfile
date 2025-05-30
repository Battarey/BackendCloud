# Using the Official Python Image
FROM python:3.11-slim

# Setting the working directory in the container
WORKDIR /app

# Copying the dependencies file
COPY requirements.txt .

# Install dependencies
# --no-cache-dir to not store pip cache
# --default-timeout=100 in case of slow connection
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy all application code to the working directory
COPY . .

# Default command to run the application (can be overridden in docker-compose)
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]