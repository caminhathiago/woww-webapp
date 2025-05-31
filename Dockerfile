FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy everything (setup.py, requirements.txt, src/)
COPY . .

# Install pip dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install your package (woww from setup.py and src/)
RUN pip install .

# Expose Dash default port
EXPOSE 8050

# Run the app
CMD ["python", "app.py"]
