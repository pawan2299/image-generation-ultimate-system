# [R&D CONTEXT]: Using python-slim to keep the deployment size under 100MB
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that Render will map
EXPOSE 8000

# Command to run the bot
CMD ["python", "main.py"]
