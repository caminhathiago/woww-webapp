# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port (Dash defaults to 8050)
EXPOSE 8050

# Command to run the app
CMD ["python", "app.py"]
