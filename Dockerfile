# Use official Python image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set workdir
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /app/

# Copy script and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run script first when container starts
ENTRYPOINT ["/entrypoint.sh"]

# Start server
CMD ["python", "-m", "daphne", "-b", "0.0.0.0", "-p", "8080", "referee.asgi:application"]
# Expose port
EXPOSE 8080