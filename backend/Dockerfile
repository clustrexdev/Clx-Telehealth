FROM python:3.11-slim

# Install required system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libxml2 \
    libxslt1.1 \
    ffmpeg \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install AWS Lambda Runtime Interface Client
RUN pip install --no-cache-dir awslambdaric

# Set Fontconfig cache path
ENV XDG_CACHE_HOME=/tmp

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .


# Set handler and entrypoint for Lambda
CMD ["modul.handler"]
ENTRYPOINT ["/usr/local/bin/python3", "-m", "awslambdaric"]

