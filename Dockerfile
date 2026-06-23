# Use a lightweight Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency list first (for faster rebuilds)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Tell Cloud Run which port to use
ENV PORT=8080

# Add gunicorn for production-ready serving
RUN pip install gunicorn

# Run the app with gunicorn instead of python main.py
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app