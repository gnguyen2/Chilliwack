FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc-dev \
    gcc \
    g++ \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft ODBC Driver 18 for SQL Server
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    apt-get remove -y libodbc2 libodbcinst2 unixodbc-common && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Set environment variables
ENV ACCEPT_EULA=Y
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 5000

# Environment for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run app
CMD ["flask", "run"]
